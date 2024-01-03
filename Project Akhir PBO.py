import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox, QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox, QComboBox

import mysql.connector

class Car:
    def __init__(self, brand, model, year, price_per_day):
        self.brand = brand
        self.model = model
        self.year = year
        self.price_per_day = price_per_day
        self.is_available = True


class RentalApp(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        self.setWindowTitle("App Rental Mobil")
        self.connection = connection
        self.cars = []  # Initialize the cars list

        if self.connection.is_connected():
            print("Berhasil terhubung ke database")
            self.inisialisasi_db()  # Call database initialization method
            self.init_appearance()
        else:
            QMessageBox.critical(self, "Kesalahan", "Gagal terhubung ke database.")
            sys.exit()

    def inisialisasi_db(self):
        cursor = self.connection.cursor()

        create_table_query = """
            CREATE TABLE IF NOT EXISTS data_user (
                id_nama INT AUTO_INCREMENT PRIMARY KEY,
                id_nomor INT,
                id_email VARCHAR(30),
                durasi_peminjaman DATETIME
            );
        """
        cursor.execute(create_table_query)

        self.connection.commit()
        cursor.close()

    def init_appearance(self):
        layout = QVBoxLayout()

        self.label = QLabel("Mobil Yang Tersedia:")
        layout.addWidget(self.label)

        self.button_rent = QPushButton("Pemesanan")
        self.button_rent.clicked.connect(self.rent_car)
        layout.addWidget(self.button_rent)

        self.button_return = QPushButton("Pengembalian")
        self.button_return.clicked.connect(self.return_car)
        layout.addWidget(self.button_return)

        self.button_show_rentals = QPushButton("Show Rental Mobil")
        self.button_show_rentals.clicked.connect(self.show_rentals)
        layout.addWidget(self.button_show_rentals)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_car(self, car):
        self.cars.append(car)

    def update_label(self):
        available_cars = [car for car in self.cars if car.is_available]
        text = "Mobil Yang Tersedia \n"
        for car in available_cars:
            text += f"{car.brand} {car.model} - {car.year} - Rp {car.price_per_day}\n"
        self.label.setText(text)

    def rent_car(self):
        dialog = RentCarDialog(self.cars, self.connection)
        if dialog.exec_() == QDialog.Accepted:
            selected_car = dialog.selected_car
            if selected_car.is_available:
                selected_car.is_available = False
                self.update_label()
                self.insert_rental_data(dialog.line_name.text(), dialog.line_nomor.text(), dialog.line_email.text(), dialog.line_duration.text())
                QMessageBox.information(self, "Success", "Mobil Telah Disewa.")
            else:
                QMessageBox.warning(self, "Error", "Mobil Telah Dipesan.")

    def return_car(self):
        dialog = ReturnCarDialog(self.cars, self.connection)
        if dialog.exec_() == QDialog.Accepted:
            selected_car = dialog.selected_car
            if not selected_car.is_available:
                selected_car.is_available = True
                self.update_label()
                QMessageBox.information(self, "Success", "Mobil Kembali Dengan Selamat.")
            else:
                QMessageBox.warning(self, "Error", "Mobil Belum Dipesan.")

    def show_rentals(self):
        dialog = ShowRentalsDialog(self.cars, self.connection)
        dialog.exec_()

    def insert_rental_data(self, name, nomor, email, duration):
        cursor = self.connection.cursor()

        insert_data_query = """
            INSERT INTO data_user (id_nomor, id_email, durasi_peminjaman)
            VALUES (%s, %s, NOW() + INTERVAL %s DAY)
        """
        data = (nomor, email, duration)
        cursor.execute(insert_data_query, data)

        self.connection.commit()
        cursor.close()


class RentCarDialog(QDialog):
    def __init__(self, cars, connection):
        super().__init__()
        self.setWindowTitle("Pemesanan")

        self.selected_car = None
        self.cars = cars
        self.connection = connection

        layout = QFormLayout()

        self.combo_car = QComboBox()
        for car in cars:
            if car.is_available:
                self.combo_car.addItem(f"{car.brand} {car.model} - {car.year}")
        layout.addRow("Select Car", self.combo_car)

        self.line_name = QLineEdit()
        layout.addRow("Masukkan Nama", self.line_name)

        self.line_nomor = QLineEdit()
        layout.addRow("Nomor", self.line_nomor)

        self.line_email = QLineEdit()
        layout.addRow("Email", self.line_email)

        self.line_duration = QLineEdit()
        layout.addRow("Durasi Peminjaman (days)", self.line_duration)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def accept(self):
        selected_car_index = self.combo_car.currentIndex()
        self.selected_car = self.cars[selected_car_index]
        super().accept()


class ReturnCarDialog(QDialog):
    def __init__(self, cars, connection):
        super().__init__()
        self.setWindowTitle("Pengembalian")

        self.selected_car = None
        self.cars = cars
        self.connection = connection

        layout = QFormLayout()

        self.combo_car = QComboBox()
        for car in cars:
            if not car.is_available:
                self.combo_car.addItem(f"{car.brand} {car.model} - {car.year}")
        layout.addRow("Select Car", self.combo_car)

        self.line_name = QLineEdit()
        layout.addRow("Masukkan Nama", self.line_name)

        self.line_email = QLineEdit()
        layout.addRow("Email", self.line_email)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def accept(self):
        selected_car_index = self.combo_car.currentIndex()
        self.selected_car = self.cars[selected_car_index]
        super().accept()


class ShowRentalsDialog(QDialog):
    def __init__(self, cars, connection):
        super().__init__()
        self.setWindowTitle("Rental")

        self.cars = cars
        self.connection = connection

        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Brand", "Model", "Year", "Price per Day"])

        rented_cars = [car for car in cars if not car.is_available]
        table.setRowCount(len(rented_cars))
        for i, car in enumerate(rented_cars):
            brand_item = QTableWidgetItem(car.brand)
            model_item = QTableWidgetItem(car.model)
            year_item = QTableWidgetItem(str(car.year))
            price_item = QTableWidgetItem(f"Rp{car.price_per_day}")
            table.setItem(i, 0, brand_item)
            table.setItem(i, 1, model_item)
            table.setItem(i, 2, year_item)
            table.setItem(i, 3, price_item)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="rental_app"
    )

    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS rental_app")
    cursor.close()

    rental_app = RentalApp(connection)

    car1 = Car("Toyota", "Avanza", 2022, 300000)
    car2 = Car("Honda", "Jazz", 2021, 350000)
    car3 = Car("Toyota", "Calya", 2018, 400000)
    car4 = Car("Suzuki", "Grand Vitara", 2023, 600000)
    car5 = Car("Toyota", "Fortuner", 2002, 900000)

    rental_app.add_car(car1)
    rental_app.add_car(car2)
    rental_app.add_car(car3)
    rental_app.add_car(car4)
    rental_app.add_car(car5)

    rental_app.update_label()
    rental_app.show()

    sys.exit(app.exec_())
