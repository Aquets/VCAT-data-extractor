print("\nInitializing the tool. Please wait...")

from extraction import extract_wikiprojects_list, full_extraction, check_connection
import shutil
import os
import pathlib
import sys


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Menus
main_menu = {
    1: "Extract data from Wikiproject",
    2: "Extract data from Custom List",
    3: "Exit",
}

wp_menu = {
    "1": "Type a Wikiproject name to extract data",
    "2": "Back",
}

extract_data_menu = {
    1: "Keep existing files and fill missing data",
    2: "Delete existing files and  extract data",
    3: "Back"
}

list_menu = {}


def print_menu(menu_options):
    print("\n")
    for key in menu_options.keys():
        print(key, '--', menu_options[key])
    print("\n")


def clear():
    os.system('cls||clear')
    print("\n")


def main():
    while True:
        print_menu(main_menu)
        try:
            option = int(input('Enter your choice: '))
        except:
            option = ""

        clear()

        # Check what choice was entered and act accordingly
        if option == 1:
            select_wp()
        elif option == 2:
            select_list()
        elif option == 3:
            print('Bye! :)')
            sys.exit()
        else:
            print(f'{Colors.WARNING}Invalid option. Please enter a number between 1 and {len(main_menu)}.{Colors.ENDC}')


def select_wp():
    while True:
        print("Extract articles from Wikiproject")
        print("Check if a Wikiproject exists at https://wp1.openzim.org/")
        print("(Wikiproject names are case sensitive)")

        print_menu(wp_menu)

        wikiproject_id = input('Select a Wikiproject: ')

        clear()

        if wikiproject_id in projects_list:
            clear()
            extract_data(project_name=wikiproject_id, project_type="wp")

        else:
            if wikiproject_id.lower() in ["2", "back"]:
                main()
            else:
                print(f'{Colors.WARNING}"{wikiproject_id}" is not a valid Wikiproject.{Colors.ENDC}')


def select_list():
    while True:
        print("Extract data from Custom List")
        print('Choose a file in "input" folder')

        print_menu(list_menu)

        try:
            option = int(input('Enter your choice: '))
        except:
            option = ""

        clear()

        if isinstance(option, int) and option < len(list_menu):
            list_name = list_menu[option][:-4]
            extract_data(project_name=list_name, project_type="list")

        elif isinstance(option, int) and option == len(list_menu):
            main()

        else:
            print(f'{Colors.WARNING}Invalid option. Please enter a number between 1 and {len(list_menu)}.{Colors.ENDC}')


def extract_data(project_name, project_type):
    while True:
        # Create project output folder
        if os.path.exists(f"output/{project_type}_{project_name}"):
            print(f'"{project_type}_{project_name}" already existing in your output folder')

            print_menu(extract_data_menu)

            try:
                option = int(input('Enter your choice: '))
            except:
                option = ""

            clear()

            # Check what choice was entered and act accordingly
            if option == 1:
                break

            elif option == 2:
                shutil.rmtree(f"output/{project_type}_{project_name}", ignore_errors=False, onerror=None)
                os.mkdir(f"output/{project_type}_{project_name}")
                break

            elif option == 3:
                main()

            else:
                print(f'{Colors.WARNING}Invalid option. Please enter a number between 1 and {len(extract_data_menu)}.{Colors.ENDC}')
        else:
            os.mkdir(f"output/{project_type}_{project_name}")
            break

    clear()
    print(f'\nExtraction of "{project_name}" started')
    full_extraction(project_name=project_name, project_type=project_type)
    print(f"\n{Colors.OKGREEN}Done!{Colors.ENDC}\n")
    input("\nPress Enter to continue...")
    clear()
    print(f'\nYou can find the output at "output/{project_type}_{project_name}/"')
    input("\nPress Enter to continue...")
    main()


if __name__ == "__main__":

    if not check_connection():
        print("\nYou need an internet connection to use this application")
        input("Press Enter to exit...")

    else:
        print("\nCollecting data. Please wait...")

        # Check if input and output folder exist
        if not os.path.exists("output"):
            os.mkdir("output")

        if not os.path.exists("input"):
            os.mkdir("input")

        # Fill list menu with files in "input" directory
        custom_lists = [str(x).split("\\")[-1] for x in pathlib.Path('input').iterdir() if str(x)[-4:] == ".csv"]

        for i, li_element in enumerate(custom_lists):
            list_menu.update({i + 1: li_element})

        list_menu.update({len(custom_lists) + 1: "Back"})

        # Extract list of existing Wikiprojects
        projects_list = extract_wikiprojects_list()

        clear()

        # Start main menu
        print("\nWelcome to the data extractor of Visual Content Assessment Tool")
        main()
