def get_trunk_interfaces(raw_trunk_output):
    """
    Process the raw output of the 'show int trunk' command and extract the trunk interface names.
    
    Expected output example:
    
    Port        Mode             Encapsulation  Status        Native vlan
    Gi7/0/2     on               802.1q         trunking      1
    Gi7/0/8     on               802.1q         trunking      1
    Gi8/1      on               802.1q         trunking      1
    Gi8/6      on               802.1q         trunking      1
    Gi8/7      on               802.1q         trunking      1
    Po1       on               802.1q         trunking      1
    
    Returns:
        list: A list of trunk interface identifiers (e.g. ['Gi7/0/2', 'Gi7/0/8', 'Gi8/1', 'Po1']).
    """
    lines = raw_trunk_output.splitlines()
    trunk_list = []
    header_found = False
    
    for line in lines:
        if not header_found:
            if line.strip().startswith("Port"):
                header_found = True
            continue
        
        if not line.strip():
            continue
        
        parts = line.split()
        if parts:
            trunk_list.append(parts[0])
    
    return trunk_list

def normalize_interface_name(interface):
    """
    Normalize an interface name from the trunk output to match the MAC address table.
    
    Examples:
      "Po1"   -> "Port-channel1"
      "Gi8/1" -> "GigabitEthernet8/1"
      "Te2/1" -> "TenGigabitEthernet2/1"
    
    If no mapping is applicable, returns the original interface.
    """
    mapping = {
        "Po": "Port-channel",
        "Gi": "GigabitEthernet",
        "Te": "TenGigabitEthernet",
        "Fa": "FastEthernet"
    }
    for prefix, full_name in mapping.items():
        if interface.startswith(prefix):
            return full_name + interface[len(prefix):]
    return interface

def process_mac_address_table(raw_mac_output, raw_trunk_output):
    """
    Process the raw output of the 'show mac address-table' command and separate the entries 
    into two sections:
    
    - "local mac addresses": entries whose interface is not in the trunk list.
    - "remotely learned mac addresses": entries whose interface is in the trunk list.
    
    Additionally:
      - Any line containing "CPU" is skipped.
      - The "local mac addresses:" section appears first in the output,
        followed by the "remotely learned mac addresses:" section.
    
    This function now handles both the short (e.g. "Po2") and long (e.g. "Port-channel2") interface names.
    
    Parameters:
        raw_mac_output (str): Raw output from "show mac address-table".
        raw_trunk_output (str): Raw output from "show int trunk".
    
    Returns:
        str: A string containing two sections with appropriate headings.
    """
    # Extract trunk interfaces from the trunk output.
    trunk_interfaces = get_trunk_interfaces(raw_trunk_output)
    
    # Create a set that includes both the raw and normalized trunk interface names.
    normalized_trunks = [normalize_interface_name(intf) for intf in trunk_interfaces]
    trunk_check_set = set(trunk_interfaces) | set(normalized_trunks)
    
    # Split the MAC table output into lines and remove empty lines.
    lines = [line for line in raw_mac_output.splitlines() if line.strip()]
    
    # Filter out header/footer lines and any lines containing "CPU".
    header_keywords = ["Mac Address", "Vlan", "----"]
    data_lines = []
    for line in lines:
        if any(keyword in line for keyword in header_keywords):
            continue
        if "CPU" in line:
            continue
        data_lines.append(line)
    
    # Separate lines based on the interface (assumed to be in the last field).
    local_macs = []
    remote_macs = []
    
    for line in data_lines:
        parts = line.split()
        if not parts:
            continue
        port = parts[-1]
        # If the port is in our check set, classify as remote.
        if port in trunk_check_set:
            remote_macs.append(line)
        else:
            local_macs.append(line)
    
    # Build the output with "local mac addresses:" appearing first.
    output_sections = []
    
    output_sections.append("local mac addresses:")
    if local_macs:
        output_sections.extend(local_macs)
    else:
        output_sections.append("No local mac addresses found.")
    
    output_sections.append("\nremotely learned mac addresses:")
    if remote_macs:
        output_sections.extend(remote_macs)
    else:
        output_sections.append("No remotely learned mac addresses found.")
    
    return "\n".join(output_sections)
