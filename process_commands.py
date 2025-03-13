def merge_wrapped_lines(raw_output):
    """
    Merge wrapped lines from the raw output.
    
    If a line starts with whitespace, it is assumed to be a continuation of the previous line.
    Returns a list of merged lines.
    """
    merged_lines = []
    current_line = ""
    for line in raw_output.splitlines():
        # If line is empty, skip it.
        if not line.strip():
            continue
        # If the line starts with whitespace, it is a continuation.
        if line[0].isspace():
            current_line += " " + line.strip()
        else:
            # If there's an existing line, append it.
            if current_line:
                merged_lines.append(current_line)
            current_line = line.strip()
    # Append the last line if exists.
    if current_line:
        merged_lines.append(current_line)
    return merged_lines

def process_cdp_neighbors(raw_output):
    """
    Process the raw output of the 'show cdp neighbors' command by:
    
    1. Moving the line that starts with "Total cdp entries displayed" to the very top
       (with two blank lines following it).
    2. Moving any lines that start with "Capability Codes:" or "Device ID" to the very bottom
       (with three blank lines preceding them).
    3. Grouping the remaining lines into these sections:
         - "sav switches": Lines that contain any of the strings "sav01", "sav02", "sav03", or "CBS350".
         - "uplink to distribution layer": Lines that contain any of the strings "LBDS", "BDS", "SBDS", "HDS", or "CPDS".
         - "WAPs": Lines that contain any of the specified WAP model identifiers.
         - "Phone Handsets": Lines that contain the string "T33".
         - "Unsorted": Lines that do not match any of the above criteria.
    4. Appending a count for WAPs and Phone Handsets sections.
    
    Parameters:
        raw_output (str): The raw output from the 'show cdp neighbors' command.
    
    Returns:
        str: The fully processed output.
    """
    # Helper: merge wrapped lines.
    def merge_wrapped_lines(raw):
        merged_lines = []
        current_line = ""
        for line in raw.splitlines():
            if not line.strip():
                continue
            if line[0].isspace():
                current_line += " " + line.strip()
            else:
                if current_line:
                    merged_lines.append(current_line)
                current_line = line.strip()
        if current_line:
            merged_lines.append(current_line)
        return merged_lines

    # First, merge any wrapped lines.
    merged_lines = merge_wrapped_lines(raw_output)
    
    # Initialize containers for special lines.
    top_line = None
    bottom_lines = []
    main_lines = []
    
    # Separate special lines from the main output.
    for line in merged_lines:
        # Check for top line.
        if line.startswith("Total cdp entries displayed"):
            top_line = line
        # Check for bottom lines.
        elif line.startswith("Capability Codes:") or line.startswith("Device ID"):
            bottom_lines.append(line)
        else:
            main_lines.append(line)
    
    # Define keywords for each category.
    sav_keywords = ["sav01", "sav02", "sav03", "CBS350","SAV01","SAV02","SAV03"]
    uplink_keywords = ["LBDS", "BDS", "SBDS", "HDS", "CPDS"]
    wap_models = ["C9120AXI", "C9130A", "C9120A","CW9166I","AIR-AP"]
    phone_keyword = "T33"
    
    # Process the main lines into categories.
    sav_switches = []
    uplinks = []
    waps = []
    phone_handsets = []
    unsorted = []
    
    for line in main_lines:
        # Check for sav switches first.
        if any(keyword in line for keyword in sav_keywords):
            sav_switches.append(line)
        # Next, check for uplink to distribution layer.
        elif any(keyword in line for keyword in uplink_keywords):
            uplinks.append(line)
        # Then check for WAP models.
        elif any(model in line for model in wap_models):
            waps.append(line)
        # Then check for phone handsets.
        elif phone_keyword in line:
            phone_handsets.append(line)
        else:
            unsorted.append(line)
    
    # Build the output sections.
    output_sections = []
    
    # Add top line if present.
    if top_line:
        output_sections.append(top_line)
    else:
        output_sections.append("Total cdp entries displayed: N/A")
    
    # Two blank lines after top line.
    output_sections.append("")
    output_sections.append("")
    
    # WAPs section with count.
    output_sections.append("WAPs:")
    if waps:
        output_sections.extend(waps)
    else:
        output_sections.append("No WAP entries found.")
    output_sections.append(f"Total number of WAPs: {len(waps)}")
    
    # Phone Handsets section with count.
    output_sections.append("\nPhone Handsets:")
    if phone_handsets:
        output_sections.extend(phone_handsets)
    else:
        output_sections.append("No phone handset entries found.")
    output_sections.append(f"Total number of Phone Handsets: {len(phone_handsets)}")
    
    # sav switches section (no count).
    output_sections.append("\nsav switches:")
    if sav_switches:
        output_sections.extend(sav_switches)
    else:
        output_sections.append("No sav switch entries found.")
    
    # Uplink to distribution layer section (no count).
    output_sections.append("\nuplink to distribution layer:")
    if uplinks:
        output_sections.extend(uplinks)
    else:
        output_sections.append("No uplink entries found.")
    
    # Unsorted section.
    output_sections.append("\nUnsorted:")
    if unsorted:
        output_sections.extend(unsorted)
    else:
        output_sections.append("No unsorted entries found.")
    
    # Three blank lines before bottom special lines.
    output_sections.append("")
    output_sections.append("")
    output_sections.append("")
    
    # Append bottom special lines.
    if bottom_lines:
        output_sections.extend(bottom_lines)
    else:
        output_sections.append("No bottom special lines found.")
    
    return "\n".join(output_sections)
