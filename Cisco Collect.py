import tkinter as tk
from tkinter import messagebox
from netmiko import ConnectHandler
import datetime
import os

# Import your custom processing modules
from process_cdp_neighbors import process_cdp_neighbors  # renamed from process_commands.py
from process_mac_address_table import process_mac_address_table

def run_commands():
    # Retrieve user input from GUI fields
    hostname = hostname_entry.get()
    username = username_entry.get()
    password = password_entry.get()
    use_ssh_value = use_ssh.get()  # True if SSH checkbox is checked

    if not hostname or not username or not password:
        messagebox.showerror("Input Error", "Please fill in all fields.")
        return

    # Build the device dictionary based on the SSH option.
    device = {
        'host': hostname,
        'username': username,
        'password': password,
    }
    if use_ssh_value:
        device['device_type'] = 'cisco_ios'       # SSH connection
    else:
        device['device_type'] = 'cisco_ios_telnet'  # Telnet connection

    # Define the list of commands (or markers) to execute.
    # "sh running-config" is added as the final command.
    commands = [
        'show vlan',
        'show auth sessions',
        'process_cdp_neighbors',       # Special processing for CDP neighbors
        'filter_int_status_10mb',      # Special processing for "show int status"
        'process_mac_address_table',   # Special processing for MAC address table
        'sh running-config'            # This command is executed last
    ]

    # Mapping for marker commands to custom filename parts.
    special_command_names = {
        'filter_int_status_10mb': '10mb_interfaces',
        'process_cdp_neighbors': 'cdp_neighbors_processed',
        'process_mac_address_table': 'mac_address_table_processed'
    }

    date_str = datetime.datetime.now().strftime('%Y%m%d')
    output_dir = r"C:\Cisco Output"
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = []
    
    try:
        net_connect = ConnectHandler(**device)
        
        for command in commands:
            # Determine the filename portion.
            if command in special_command_names:
                command_filename = special_command_names[command]
            else:
                command_filename = command.replace(" ", "_").replace("/", "_").replace("|", "")
            
            filename = f"{hostname}_{date_str}_{command_filename}.txt"
            file_path = os.path.join(output_dir, filename)
            
            # Process commands based on marker.
            if command == 'process_cdp_neighbors':
                raw_output = net_connect.send_command("show cdp neighbors")
                output = process_cdp_neighbors(raw_output)
            elif command == 'filter_int_status_10mb':
                raw_output = net_connect.send_command("show int status")
                output = "\n".join(line for line in raw_output.splitlines() if "a-10 " in line)
            elif command == 'process_mac_address_table':
                trunk_raw_output = net_connect.send_command("show int trunk")
                mac_raw_output = net_connect.send_command("show mac address-table")
                output = process_mac_address_table(mac_raw_output, trunk_raw_output)
            else:
                output = net_connect.send_command(command)
            
            # Write the output to file.
            with open(file_path, "w") as file:
                file.write(output)
            output_files.append(file_path)
        
        net_connect.disconnect()
        files_message = "\n".join(output_files)
        messagebox.showinfo("Success", f"Commands executed successfully. Files created:\n{files_message}")
    
    except Exception as e:
        error_msg = str(e).lower()
        suggestion = ""
        # If the error message indicates connection refusal and SSH isn't enabled, suggest using SSH.
        if not use_ssh_value and "actively refused" in error_msg:
            suggestion = "\nIt appears that the switch may require SSH connectivity. Please try checking the 'Use SSH' option."
        messagebox.showerror("Error", f"An error occurred:\n{e}{suggestion}")

def exit_app():
    root.destroy()

# Create the main window for the GUI
root = tk.Tk()
root.title("Network Switch Command Runner")

tk.Label(root, text="Switch Hostname/IP:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
hostname_entry = tk.Entry(root, width=30)
hostname_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Username:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
username_entry = tk.Entry(root, width=30)
username_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Password:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
password_entry = tk.Entry(root, show="*", width=30)
password_entry.grid(row=2, column=1, padx=10, pady=10)

# SSH Option Checkbox
use_ssh = tk.BooleanVar()
ssh_checkbox = tk.Checkbutton(root, text="Use SSH", variable=use_ssh)
ssh_checkbox.grid(row=3, column=0, columnspan=2, pady=10)

run_button = tk.Button(root, text="Run Commands", command=run_commands)
run_button.grid(row=4, column=0, columnspan=2, pady=10)

exit_button = tk.Button(root, text="Exit", command=exit_app)
exit_button.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()