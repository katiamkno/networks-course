import os
from ftplib import FTP, error_perm

FTP_HOST = "127.0.0.1"
FTP_PORT = 21
FTP_USER = "TestUser"
FTP_PASS = ""

def connect_ftp():
    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"Connected to {FTP_HOST}:{FTP_PORT}")
        return ftp
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def list_directory(ftp):
    try:
        items = []
        ftp.retrlines('LIST', items.append)

        if not items:
            print("(empty)")
        else:
            for item in items:
                print(item)
            print(f"\nTotal items: {len(items)}")

    except error_perm as e:
        print(f"Permission error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def upload_file(ftp):
    local_path = input("\nEnter path to local file: ").strip().strip('"')

    if not os.path.exists(local_path):
        print("File not found!")
        return

    if not os.path.isfile(local_path):
        print("Not a file!")
        return

    filename = os.path.basename(local_path)
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        print(f"File '{filename}' successfully uploaded to server")
    except error_perm as e:
        print(f"Permission error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def download_file(ftp):
    filename = input("\nEnter filename on server: ").strip()

    if not filename:
        print("Filename cannot be empty")
        return

    save_path = input("Enter save path (Enter = current directory): ").strip()

    if not save_path:
        save_path = os.path.join(os.getcwd(), filename)
    elif os.path.isdir(save_path):
        save_path = os.path.join(save_path, filename)

    try:
        with open(save_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        print(f"File saved: {save_path}")
    except error_perm as e:
        print(f"Permission error (file may not exist): {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    FTP_PASS = input("Enter FTP password: ").strip()
    ftp = connect_ftp()
    if ftp is None:
        print("\nCheck connection settings and make sure server is running.")
        return

    try:
        while True:
            print("Select action:")
            print("1 - List files and directories")
            print("2 - Upload file to server")
            print("3 - Download file from server")
            print("0 - Exit")

            choice = input("> ").strip()

            if choice == "1":
                list_directory(ftp)
            elif choice == "2":
                upload_file(ftp)
            elif choice == "3":
                download_file(ftp)
            elif choice == "0":
                print("\nExiting...")
                break
            else:
                print("Invalid choice! Enter 1, 2, 3 or 0.")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        try:
            ftp.quit()
        except:
            ftp.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()