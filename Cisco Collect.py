import tkinter as tk
from tkinter import messagebox
from netmiko import ConnectHandler
import datetime
import os

# Import your custom modules/functions
from process_commands import process_cdp_neighbors  # Your existing module for CDP processing
from process_mac_address_table import process_mac_address_table  # Module for MAC table processing

def run_commands():
    # Retrieve user input from GUI fields
    hostname = hostname_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if not hostname or not username or not password:
        messagebox.showerror("Input Error", "Please fill in all fields.")
        return

    device = {
        'device_type': 'cisco_ios_telnet',
        'host': hostname,
        'username': username,
        'password': password,
    }

    # Define the list of commands (markers) to execute.
    # "sh running-config" is added as the final command.
    commands = [
        'show vlan',
        'show auth sessions',
        'process_cdp_neighbors',       # For processed CDP neighbors
        'filter_int_status_10mb',      # For filtered "show int status"
        'process_mac_address_table',   # For MAC address table processing
        'sh running-config'            # For running configuration; this is executed last.
    ]

    # Mapping for markers to custom filename strings.
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
        # Connect to the device once
        net_connect = ConnectHandler(**device)
        
        for command in commands:
            # Determine the filename portion.
            if command in special_command_names:
                command_filename = special_command_names[command]
            else:
                # For standard commands, sanitize the command for filename use.
                command_filename = command.replace(" ", "_").replace("/", "_").replace("|", "")
            
            filename = f"{hostname}_{date_str}_{command_filename}.txt"
            file_path = os.path.join(output_dir, filename)
            
            # Process each command based on its marker.
            if command == 'process_cdp_neighbors':
                raw_output = net_connect.send_command("show cdp neighbors")
                output = process_cdp_neighbors(raw_output)
            
            elif command == 'filter_int_status_10mb':
                raw_output = net_connect.send_command("show int status")
                output = "\n".join(
                    line for line in raw_output.splitlines() if "a-10 " in line
                )
            
            elif command == 'process_mac_address_table':
                trunk_raw_output = net_connect.send_command("show int trunk")
                mac_raw_output = net_connect.send_command("show mac address-table")
                output = process_mac_address_table(mac_raw_output, trunk_raw_output)
            
            else:
                # For normal commands, simply send the command.
                output = net_connect.send_command(command)
            
            # Write the output to a file.
            with open(file_path, "w") as file:
                file.write(output)
            
            output_files.append(file_path)
        
        net_connect.disconnect()
        files_message = "\n".join(output_files)
        messagebox.showinfo("Success", f"Commands executed successfully. Files created:\n{files_message}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

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

run_button = tk.Button(root, text="Run Commands", command=run_commands)
run_button.grid(row=3, column=0, columnspan=2, pady=10)

exit_button = tk.Button(root, text="Exit", command=exit_app)
exit_button.grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
