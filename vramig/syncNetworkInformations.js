
var vra = System.getModule("com.vmk").VraManager();
var ipAddr = System.getModule("com.vmk.common").IPAddr();

var ranges = [];
for each(var range in vra.getUerp("/provisioning/uerp/resources/subnet-ranges?expand&$top=10000").documents) {
    ranges.push({
        ipStt: ipAddr.ip2num(range.startIPAddress),
        ipEnd: ipAddr.ip2num(range.endIPAddress),
        subnetRangeLink: range.documentSelfLink,
        subnetLink: range.subnetLink
    });
}

for each(var vm in vra.getUerp("/resources/compute?expand&$filter=((lifecycleState eq 'READY') and (type eq 'VM_GUEST'))").documents) {
    try { vm = VcPlugin.getAllVirtualMachines(null, vm.name)[0]; }
    catch (e) { continue }
    for each(var nic in vm.guest.net) {
        var netif = vra.getUerp("/resources/network-interfaces?expand&$filter=(customProperties.mac_address eq '" + nic.macAddress + "')");
        if (netif.totalCount == 1) {
            netif = netif.documents[netif.documentLinks[0]];
        } else {
            System.log("! could not find mac[" + nic.macAddress + "]");
            continue;
        }
        var networkInterfaceLink = netif.documentSelfLink;
        var addressLinks = [];
        var addressTitle = "";
        var subnetTitleLink = null;
        var subnetTitleName = null;
        if (nic.ipConfig != null) {
            for each(var ipObj in nic.ipConfig.ipAddress) {
                var ipAddress = ipObj.ipAddress;
                if (ipAddress.indexOf(":") > -1) { continue; } // ipv6 not support
                var ipAddressNum = ipAddr.ip2num(ipAddress);
                for each(var range in ranges) {
                    if (ipAddressNum >= range.ipStt && ipAddressNum <= range.ipEnd) {
                        var subnetLink = range.subnetLink;
                        var subnet = vra.getUerp("/resources/sub-networks?expand&$filter=(documentSelfLink eq '" + subnetLink + "')");
                        if (subnet.totalCount == 1) {
                            subnet = subnet.documents[subnet.documentLinks[0]];
                        } else {
                            System.log("! could not find subnet[" + subnetLink + "] in range[" + ipAddr.num2ip(range.ipStt) + "~" + ipAddr.num2ip(range.ipEnd) + "]");
                            break;
                        }
                        var subnetRangeLink = range.subnetRangeLink;
                        var checkIp = vra.getUerp("/resources/ip-addresses?expand&$filter=((subnetRangeLink eq '" + subnetRangeLink + "') and (ipAddress eq '" + ipAddress + "'))");
                        if (checkIp.totalCount == 0) { // post
                            try{
                                addressLinks.push(vra.post("/provisioning/uerp/resources/ip-addresses", {
                                    "customProperties": {},
                                    "ipAddress": ipAddress,
                                    "ipAddressStatus": "ALLOCATED",
                                    "subnetRangeLink": subnetRangeLink,
                                    "connectedResourceLink": networkInterfaceLink
                                }).documentSelfLink);
                                if (addressTitle == "") { addressTitle = ipAddress; }
                                if (subnetTitleLink == null) { subnetTitleLink = subnetLink; }
                                if (subnetTitleName == null) { subnetTitleName = subnet.name; }
                            } catch (e) { System.log(e); }
                        } else if (checkIp.totalCount == 1) {
                            checkIp = checkIp.documents[checkIp.documentLinks[0]];
                            if (checkIp.ipAddressStatus != "ALLOCATED") { // patch
                                checkIp.ipAddressStatus = "ALLOCATED";
                                checkIp.connectedResourceLink = networkInterfaceLink;
                                try {
                                    addressLinks.push(vra.patch("/provisioning/uerp" + checkIp.documentSelfLink, checkIp).documentSelfLink);
                                    if (addressTitle == "") { addressTitle = ipAddress; }
                                    if (subnetTitleLink == null) { subnetTitleLink = subnetLink; }
                                    if (subnetTitleName == null) { subnetTitleName = subnet.name; }
                                } catch (e) { System.log(e); }
                            } else {
                                System.log("ip[" + ipAddress + "] is already allocated");
                            }
                        }
                        break;
                    }
                }
            }
        }

        if (subnetTitleLink != null) { netif.subnetLink = subnetTitleLink; }
        if (netif.name.indexOf("Network adapter") > -1) { netif.deviceIndex = Number(netif.name.split("adapter ")[1]) - 1; }
        if (subnetTitleName != null) { netif.name = subnetTitleName; }
        netif.addressLinks = addressLinks;
        netif.address = addressTitle;
        vra.put("/provisioning/uerp" + netif.documentSelfLink, netif);
    }
}