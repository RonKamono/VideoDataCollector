import flet as ft

from config.settings import WindowsSize, Colors

from app.application_page import AppPage

class App:
    def __init__(self):
        self.window_size = WindowsSize()
        self.colors = Colors

    async def main(self, page: ft.Page):
        await page.window.center()
        page.window.width = self.window_size.window_width
        page.window.height = self.window_size.window_height
        page.bgcolor = self.colors.color_bg
        main_container = ft.Container(expand=True)

        app_page = AppPage(page ,self.colors)

        main_container.content = app_page.application_page

        page.add(main_container)



if __name__ == '__main__':
    application = App()
    ft.run(main=application.main)