import ipaddress as ipa

networks = [ipa.ip_network('10.9.0.0/24'),
            ipa.ip_network('fdfd:87b5:b475:5e3e::/64')]

addresses = [ipa.ip_address('10.9.0.6'),
             ipa.ip_address('10.7.0.31'),
             ipa.ip_address('fdfd:87b5:b475:5e3e:b1bc:e121:a8eb:14aa'),
             ipa.ip_address('fe80::3840:c439:b25e:63b0')]

for ip in addresses:
    for net in networks:
        if ip in net:
            print(f'{ip}\nis on {net}')
            break
    else:
        print(f'{ip}\nis not on a known network')
    print()

