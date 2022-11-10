import os
import readline  # noqa, to fix bug with max 1024 len input for macos

from simple_term_menu import TerminalMenu

from extractor import Extractor, CWD


def say_hello():
    """
    Welcome message
    """

    print(f"""
    Вітання у пілотній версії Collaborator Extractor!
    
    Author: Roman Skok <romeskq> <rma.skok@gmail.com>
    p.s: made with love for uuliankaa <3
    
    {'▰▰▰▰▰' * 10}
    
    """)


def check_existing_sessions() -> dict:

    sessions_folder_path = os.path.join(CWD, 'sessions')
    if not os.path.exists(sessions_folder_path):
        return {}

    sessions = os.listdir(sessions_folder_path)
    sessions.append('* use another')

    terminal_menu = TerminalMenu(sessions)

    print("\nЗнайдено збережені сессії. Виберіть одну використовуючи стрілочки: ")
    menu_choice = terminal_menu.show()  # return index of element

    if menu_choice == len(sessions) - 1:
        return {}

    return {
        'cookies': os.path.join(sessions_folder_path, sessions[menu_choice])
    }


def get_user_data() -> dict:

    print("\n Введіть ваші дані для входу. В майбутньому ви зможете використовувати вже збережені сессії.")

    user_login = input("[login]: ")
    user_password = input("[password]: ")

    return {
        'login': user_login,
        'password': user_password,
    }


def main() -> None:

    say_hello()

    user_data = check_existing_sessions() or get_user_data()

    collaborator_url = input("\n[url to parse]: ")
    user_data['url'] = collaborator_url

    extractor = Extractor(user_data)
    extractor.start()

    print("Завершення програми.")


if __name__ == "__main__":
    main()
