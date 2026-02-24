import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame,
    QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QSplitter, QGroupBox, QSpinBox, QDoubleSpinBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


# -------------------------- CONFIGURACIÓN --------------------------
CONFIG = {
    "BASE_API_URL": "http://localhost:3001/api",
    "LOCAL_BANKS": [
        "Banco de Venezuela", "Banesco", "Mercantil Banco",
        "BBVA Provincial", "Banco del Tesoro", "Banco Caroní"
    ],
    "DEFAULT_EXCHANGE_RATE": 36.5,
    "CURRENCIES": [("usd", "Dólar Estadounidense"), ("bs", "Bolívar Soberano")],
    "WINDOW_SIZE": (1024, 768),
    "PRODUCT_CATEGORIES": ["Alimentos", "Bebidas", "Limpieza", "Farmacia", "Otros"]
}


# -------------------------- VENTANA DE LOGIN --------------------------
class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("POS Venezuela - Iniciar Sesión")
        self.setFixedSize(350, 250)
        self.user = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel("SISTEMA POS VENEZUELA")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Correo electrónico")
        self.email_input.setFont(QFont("Arial", 14))
        self.email_input.setStyleSheet("padding: 8px; border-radius: 4px; border: 1px solid #ddd;")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 14))
        self.password_input.setStyleSheet("padding: 8px; border-radius: 4px; border: 1px solid #ddd;")
        layout.addWidget(self.password_input)

        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setFont(QFont("Arial", 14))
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
        """)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Advertencia", "Completa todos los campos")
            return

        try:
            response = requests.post(
                f"{CONFIG['BASE_API_URL']}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.user = data["user"]
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Credenciales incorrectas")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error", "No hay conexión con el servidor\nPuedes usar el modo offline temporalmente")
            self.user = {"name": "Usuario Prueba"}
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")


# -------------------------- DASHBOARD --------------------------
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.current_rate = CONFIG["DEFAULT_EXCHANGE_RATE"]
        self.stats = {
            "total_sales_usd": 0.0, "total_sales_bs": 0.0,
            "today_sales_usd": 0.0, "today_sales_bs": 0.0,
            "active_customers": 0, "pending_credit_usd": 0.0,
            "pending_credit_bs": 0.0, "total_products": 0
        }
        self.init_ui()
        self.load_data()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(300000)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("PANEL PRINCIPAL")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        self.rate_label = QLabel(f"Tasa de Cambio: 1 USD = {self.current_rate:.2f} Bs")
        self.rate_label.setFont(QFont("Arial", 14))
        self.rate_label.setStyleSheet("color: #4b5563; margin-bottom: 10px;")
        main_layout.addWidget(self.rate_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        grid_layout.addWidget(self.create_stat_card("VENTAS TOTALES", f"{self.stats['total_sales_usd']:.2f} USD", f"{self.stats['total_sales_bs']:.2f} Bs"), 0, 0)
        grid_layout.addWidget(self.create_stat_card("VENTAS DE HOY", f"{self.stats['today_sales_usd']:.2f} USD", f"{self.stats['today_sales_bs']:.2f} Bs"), 0, 1)
        grid_layout.addWidget(self.create_stat_card("CLIENTES ACTIVOS", str(self.stats['active_customers']), ""), 1, 0)
        grid_layout.addWidget(self.create_stat_card("CRÉDITO PENDIENTE", f"{self.stats['pending_credit_usd']:.2f} USD", f"{self.stats['pending_credit_bs']:.2f} Bs"), 1, 1)
        grid_layout.addWidget(self.create_stat_card("PRODUCTOS REGISTRADOS", str(self.stats['total_products']), ""), 2, 0)
        grid_layout.addWidget(self.create_stat_card("MODO DE TRABAJO", "OFFLINE", "Sin conexión al servidor"), 2, 1)

        main_layout.addLayout(grid_layout)

    def create_stat_card(self, title, value1, value2):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #eee;
            }
        """)
        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13))
        title_label.setStyleSheet("color: #6b7280; margin-bottom: 8px;")
        layout.addWidget(title_label)

        value1_label = QLabel(value1)
        value1_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        layout.addWidget(value1_label)

        if value2:
            value2_label = QLabel(value2)
            value2_label.setFont(QFont("Arial", 12))
            value2_label.setStyleSheet("color: #4b5563;")
            layout.addWidget(value2_label)

        return frame

    def load_data(self):
        try:
            rate_res = requests.get(f"{CONFIG['BASE_API_URL']}/exchange")
            if rate_res.status_code == 200:
                self.current_rate = rate_res.json()["rate"]
                self.rate_label.setText(f"Tasa de Cambio: 1 USD = {self.current_rate:.2f} Bs")

            stats_res = requests.get(f"{CONFIG['BASE_API_URL']}/stats")
            if stats_res.status_code == 200:
                self.stats = stats_res.json()
                self.update_card_values()
                # Actualizar modo de trabajo a ONLINE
                self.layout().itemAt(2).layout().itemAt(5).widget().layout().itemAt(1).widget().setText("ONLINE")
        except:
            pass

    def update_card_values(self):
        grid_layout = self.layout().itemAt(2).layout()
        self.update_single_card(grid_layout.itemAt(0).widget(), f"{self.stats['total_sales_usd']:.2f} USD", f"{self.stats['total_sales_bs']:.2f} Bs")
        self.update_single_card(grid_layout.itemAt(1).widget(), f"{self.stats['today_sales_usd']:.2f} USD", f"{self.stats['today_sales_bs']:.2f} Bs")
        self.update_single_card(grid_layout.itemAt(2).widget(), str(self.stats['active_customers']), "")
        self.update_single_card(grid_layout.itemAt(3).widget(), f"{self.stats['pending_credit_usd']:.2f} USD", f"{self.stats['pending_credit_bs']:.2f} Bs")
        self.update_single_card(grid_layout.itemAt(4).widget(), str(self.stats['total_products']), "")

    def update_single_card(self, card_widget, value1, value2):
        layout = card_widget.layout()
        layout.itemAt(1).widget().setText(value1)
        if value2 and layout.count() > 2:
            layout.itemAt(2).widget().setText(value2)


# -------------------------- GESTIÓN DE TASA DE CAMBIO --------------------------
class ExchangeRateManager(QWidget):
    def __init__(self):
        super().__init__()
        self.current_rate = CONFIG["DEFAULT_EXCHANGE_RATE"]
        self.init_ui()
        self.load_current_rate()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("GESTIÓN DE TASA DE CAMBIO")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #eee;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        rate_label = QLabel("Tasa USD a Bolívar Soberano:")
        rate_label.setFont(QFont("Arial", 14))
        form_layout.addWidget(rate_label)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setDecimals(2)
        self.rate_input.setMinimum(0.01)
        self.rate_input.setMaximum(9999.99)
        self.rate_input.setFont(QFont("Arial", 14))
        self.rate_input.setStyleSheet("padding: 8px; border-radius: 4px; border: 1px solid #ddd;")
        form_layout.addWidget(self.rate_input)

        update_btn = QPushButton("Actualizar Tasa")
        update_btn.setFont(QFont("Arial", 14))
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        update_btn.clicked.connect(self.handle_update)
        form_layout.addWidget(update_btn)

        # Nueva función: Calcular precio en Bs a partir de USD
        calc_group = QGroupBox("Calculadora Rápida")
        calc_group.setFont(QFont("Arial", 12))
        calc_layout = QHBoxLayout(calc_group)
        
        self.usd_calc_input = QDoubleSpinBox()
        self.usd_calc_input.setDecimals(2)
        self.usd_calc_input.setMinimum(0.01)
        self.usd_calc_input.setMaximum(9999.99)
        self.usd_calc_input.setPrefix("USD ")
        self.usd_calc_input.valueChanged.connect(self.calculate_bs)
        
        self.bs_calc_label = QLabel("Bs 0.00")
        self.bs_calc_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        
        calc_layout.addWidget(self.usd_calc_input)
        calc_layout.addWidget(self.bs_calc_label)
        form_layout.addWidget(calc_group)

        main_layout.addWidget(form_frame)

    def load_current_rate(self):
        try:
            response = requests.get(f"{CONFIG['BASE_API_URL']}/exchange")
            if response.status_code == 200:
                self.current_rate = response.json()["rate"]
                self.rate_input.setValue(self.current_rate)
            else:
                self.rate_input.setValue(CONFIG["DEFAULT_EXCHANGE_RATE"])
        except:
            self.rate_input.setValue(CONFIG["DEFAULT_EXCHANGE_RATE"])

    def handle_update(self):
        try:
            new_rate = self.rate_input.value()
            self.current_rate = new_rate
            # Guardar en servidor si hay conexión
            try:
                requests.put(
                    f"{CONFIG['BASE_API_URL']}/exchange",
                    json={"rate": new_rate}
                )
                QMessageBox.information(self, "Éxito", "Tasa actualizada correctamente y guardada en servidor")
            except:
                QMessageBox.information(self, "Éxito", "Tasa actualizada localmente (sin conexión al servidor)")
            # Actualizar calculadora
            self.calculate_bs()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la tasa: {str(e)}")

    def calculate_bs(self):
        usd_value = self.usd_calc_input.value()
        bs_value = usd_value * self.current_rate
        self.bs_calc_label.setText(f"Bs {bs_value:.2f}")


# -------------------------- GESTIÓN DE PRODUCTOS --------------------------
class ProductsManager(QWidget):
    def __init__(self):
        super().__init__()
        self.products = [
            # Datos de prueba para cuando no haya conexión
            {"id": 1, "name": "Coca-Cola 600ml", "category": "Bebidas", "price_usd": 0.50, "price_bs": 18.25, "stock": 50},
            {"id": 2, "name": "Pan Blanco 1kg", "category": "Alimentos", "price_usd": 0.30, "price_bs": 10.95, "stock": 30}
        ]
        self.init_ui()
        self.load_products()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("GESTIÓN DE PRODUCTOS")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        main_layout.addWidget(title_label)

        # Formulario
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
