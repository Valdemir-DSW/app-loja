import sys
import os
import subprocess
import webbrowser
from PyQt5.QtCore import QUrl, Qt, QDateTime, QSettings
from PyQt5.QtWidgets import QApplication, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QHBoxLayout, \
    QWidget, QLabel, QStackedWidget, QMessageBox, QCheckBox, QFileDialog, QAction,QFileIconProvider
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtGui import QIcon
class AppStore(QMainWindow):
    def __init__(self):
        super().__init__()

        self.browser = QWebEngineView()
        self.browser.setFixedSize(600, 600)
        self.browser.setUrl(QUrl("http://193.34.77.114/"))

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.browser)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('⚙')

        # Adicionando ação "Fechar"
        ehelp = QAction('help', self)
        ehelp.triggered.connect(self.help)
        fileMenu.addAction(ehelp) 
        ehelp1 = QAction('cache de donwload', self)
        ehelp1.triggered.connect(self.cache)
        fileMenu.addAction(ehelp1) 
      
        fileMenu.addSeparator()
        fileMenu.addSeparator() 
        exitAction = QAction('Fechar app', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction) 

            
       

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setValue(0)

        self.download_button = QPushButton("🔄")
        self.download_button.clicked.connect(self.reload_page)

        self.back_button = QPushButton("<")
        self.back_button.clicked.connect(self.browser.back)

        self.forward_button = QPushButton(">")
        self.forward_button.clicked.connect(self.browser.forward)

        self.toggle_download_button = QPushButton("Downloads (0 em andamento)")
        self.toggle_download_button.clicked.connect(self.toggle_download_view)
        self.toggle_download_button.setMaximumWidth(250)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.download_button)
        progress_layout.addWidget(self.back_button)
        progress_layout.addWidget(self.forward_button)
        progress_layout.addWidget(self.toggle_download_button)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        layout.addLayout(progress_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignBottom)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        self.setFixedSize(self.sizeHint())

        self.browser.page().profile().downloadRequested.connect(self.download_requested)
        self.browser.page().loadProgress.connect(self.update_progress)

        # Conectar os sinais da janela para salvar e carregar a posição
        self.closeEvent = self.save_window_position
        self.showEvent = self.load_window_position

        self.setWindowTitle("App Store")
        self.show()

        self.download_count = 0
        self.downloads = []
        self.var = None

        # Criar o QCheckBox no método __init__
        self.init_download_view()
    
    def cache(self):
        download_dir = os.path.join(os.getcwd(), "downloads")

        # Abre o explorador de arquivos na pasta de downloads
        if sys.platform.startswith('darwin'):
            subprocess.run(['open', download_dir])
        elif os.name == 'nt':
            os.startfile(download_dir)
        elif os.name == 'posix':
            subprocess.run(['xdg-open', download_dir])

    

    def help(self):
        help_url = "https://sites.google.com/view/dsw-wheel/p%C3%A1gina-inicial"
        webbrowser.open(help_url)
    def save_window_position(self, event):
        # Salvar a posição da janela no app data
        settings = QSettings("organization", "app")
        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("window/state", self.saveState())

    def load_window_position(self, event):
        # Carregar a posição da janela do app data
        settings = QSettings("organization", "app")
        geometry = settings.value("window/geometry")
        state = settings.value("window/state")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

    def download_requested(self, download):
        # Verificar se o download já está na lista ou já foi concluído
        if download not in [d['download_item'] for d in self.downloads] and not download.isFinished():
            download.finished.connect(self.download_finished)
            self.download_count += 1
            download.setSavePageFormat(QWebEngineDownloadItem.CompleteHtmlSaveFormat)

            # Especificar o caminho completo do arquivo de destino
            download_dir = os.path.join(os.getcwd(), "downloads")
            os.makedirs(download_dir, exist_ok=True)
            file_name = os.path.join(download_dir, download.url().fileName())
            download.setPath(file_name)

            # Adicionar o download à lista
            self.downloads.append({
                'download_item': download,
                'status': 'Andamento',
                'start_time': QDateTime.currentDateTime(),
                'estimated_time': -1  # A ser calculado
            })

            download.accept()

            # Atualizar a tela de downloads
            self.update_download_screen()

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def reload_page(self):
        self.browser.reload()

    def init_download_view(self):
        self.download_widget = QWidget()
        self.download_layout = QVBoxLayout()

        self.download_widget.setLayout(self.download_layout)
        self.stacked_widget.addWidget(self.download_widget)

    def toggle_download_view(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index == 0:
            self.stacked_widget.setCurrentIndex(1)
            self.toggle_download_button.setText("Voltar a loja")
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.toggle_download_button.setText(f"Downloads ({self.download_count} em andamento)")

    def download_finished(self):
        # Remover downloads concluídos da lista
        self.downloads = [download for download in self.downloads if not download['download_item'].isFinished()]

        self.download_count = len(self.downloads)

        # Atualizar a tela de downloads
        self.update_download_screen()

        # Exibir mensagem de conclusão do download
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("O arquivo foi baixado com sucesso!")
        msg.setWindowTitle("Download Concluído")
        msg.exec_()

        # Executar automaticamente, se a opção estiver marcada
        self.execute_downloads()

    def update_download_screen(self):
        # Limpar a tela de downloads
        for i in reversed(range(self.download_layout.count())):
            item = self.download_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        # Adicionar os downloads à tela
        for download in self.downloads:
            self.var = download['download_item'].path()
            download_label = QLabel(self.format_download_info(download))
            execute_button = QPushButton("Executar")
            execute_button.clicked.connect(lambda _, d=download: self.execute_single_download(d))
            move_button = QPushButton("Mover para...")
            move_button.clicked.connect(lambda _, d=download: self.move_single_download(d))
            download_layout = QHBoxLayout()
            download_layout.addWidget(download_label)
            download_layout.addWidget(execute_button)
            download_layout.addWidget(move_button)
            self.download_layout.addLayout(download_layout)

        self.toggle_download_button.setText(f"Downloads ({self.download_count} em andamento)")

    def execute_single_download(self, download):
        os.startfile(download['download_item'].path())

    def move_single_download(self, download):
        # Solicitar ao usuário um novo local para o download
        new_path, _ = QFileDialog.getSaveFileName(self, 'Escolher novo local para o download', '', 'Todos os arquivos (*.*);;')
        if new_path:
            # Mover o arquivo para o novo local
            os.replace(download['download_item'].path(), new_path)

    def execute_downloads(self):
        print("bom dia")
        os.startfile(self.var)

    def format_download_info(self, download):
        file_name = download['download_item'].url().fileName()
        status = download['status']
        start_time = download['start_time']
        estimated_time = download['estimated_time']

        if estimated_time == -1:
            estimated_time_str = "Calculando..."
        else:
            estimated_time_str = f"Tempo estimado: {estimated_time} segundos"

        return f" Arquivo: {file_name} \n Status: sem erros \n Iniciado em: {start_time.toString(Qt.DefaultLocaleLongDate)} - {estimated_time_str}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("App Store")
    app.setWindowIcon(QIcon(os.path.abspath("ICO.ico")))
    window = AppStore()
    sys.exit(app.exec_())
