This Python script pops up a simple GUI, allowing the user to enter switch name, Username, Password. It then logs onto the switch and grabs the following;


Unprocessed;

Show Vlan
Show running config
show auth sessions
List of 10mb connected interfaces

Processed;

Show mac address table
    groups the 'local' mac addresses together and also groups the remote (learned via Trunk) mac addresses together
show cdp neighbors
    groups WAPs, Phones, Savs, uplinks, other for easier viewing

Features to be added;

Option to use SSH - will be needed for some of our switches that are set for SSH only
List of 'non-standard' interface (ie interfaces with a specific description (like a UPS) or interface not using MAB/dot1x)

