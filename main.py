import os

from sys import platform

if platform == "darwin":
    import readline  # noqa, to fix bug with max 1024 len input for macos

if platform != "win32":
    from simple_term_menu import TerminalMenu

from extractor import Extractor, CWD


def say_hello():
    """
    Welcome message
    """

    print(f"""
    Вітання у Collaborator Extractor!
    
    Author: Roman Skok <romeskq> <rma.skok@gmail.com>
    p.s: made with love for uuliankaa <3
    
    {'--' * 10}
    
    """)


def check_existing_sessions() -> dict:

    sessions_folder_path = os.path.join(CWD, 'sessions')
    if not os.path.exists(sessions_folder_path):
        return {}

    sessions = os.listdir(sessions_folder_path)
    sessions.append('* use another')

    print("\nЗнайдено збережені сесії. Виберіть одну: ")

    if platform != "win32":
        terminal_menu = TerminalMenu(sessions)
        menu_choice = terminal_menu.show()  # return index of element
    else:
        menu = "\n".join([f"[{i}] - {text}" for i, text in enumerate(sessions)])
        print(menu)
        is_num_entered = False
        menu_choice = len(sessions) - 1

        while not is_num_entered:
            menu_choice = input("Введіть відповідне число: ")
            is_num_entered = menu_choice.isdigit() or int(menu_choice) in range(len(sessions))
        
        menu_choice = int(menu_choice)

        if menu_choice == len(sessions) - 1:
            return {}

    return {
        'cookies': os.path.join(sessions_folder_path, sessions[menu_choice])
    }


def get_user_data() -> dict:

    print("\n Введіть ваші дані для входу. В майбутньому ви зможете використовувати вже збережені сесії.")

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
