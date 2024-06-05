import requests
import csv
import dns.resolver
import dns.exception
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from time import sleep

'''https://ipinfo.io/countries/vn#section-routers'''


headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
}

'''Lấy danh sách các ASN ở Việt Nam'''
def get_asn_list_vn():
    res = requests.get(url="https://whoisrequest.com/ip/vn", headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find_all("tr")
    asn_vn_list = []
    for datas in table:
        data = datas.find_all("td")
        if len(data) == 3  and data[1].text.strip() != '':
            asn_vn_list.append({
                "asn": data[0].text.strip(),
                "organization": data[1].text.strip(),
                "ips_assigned": data[2].text.strip()
            })

    '''Lưu danh sách vào file csv'''
    with open("C:\\Users\\Admin\\Documents\\crtsh\\DS_ASN_VN.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        fields = asn_vn_list[0].keys()
        writer.writerow(fields)
        for item in asn_vn_list:
            writer.writerow(item.values())


'''Lấy danh sách ASN của các ngân hàng ở Việt Nam'''
def get_asn_bank_list():
    asn_bank_list = []
    with open("C:\\Users\\Admin\\Documents\\crtsh\\DS_ASN_VN.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0]=="asn": continue
            if row[2] != "0" and ("bank" in row[1] or "Bank" in row[1] or "BANK" in row[1]):
                asn_bank_list.append(row[0])

    with open("C:\\Users\\Admin\\Documents\\crtsh\\asn_bank_vn.txt", "w") as file:
        for i in asn_bank_list:
            file.write(i + "\n")


'''Lấy danh sách IP block của ASN'''
def get_block_list():
    asn_bank_list = get_bank_list()
    for asn in asn_bank_list:
        # print(asn)
        with open("C:\\Users\\Admin\\Documents\\crtsh\\Bank\\{}_ip_blocks.txt".format(asn), "w") as file:
            URL = "https://whoisrequest.com/ip/{}".format(asn)
            # print(URL)
            res = requests.get(url=URL, headers=headers)
            soup = BeautifulSoup(res.text, "lxml")
            tables = soup.find_all("table")
            rows = tables[0].find_all("tr")
            for row in rows:
                datas = row.find_all("td")
                if datas != []:
                    # print(datas[0].text.strip())
                    file.write(datas[0].text.strip() + "\n")

'''Tạo danh sách IP từ danh sách IP Blocks'''
def get_ip_list():
    ip_list = []
    asn_bank_list = get_bank_list()
    for asn in asn_bank_list:
        with open("C:\\Users\\Admin\\Documents\\crtsh\\Bank\\{}_ip_blocks.txt".format(asn), "r") as fr:
            lines = fr.readlines()
            for line in lines:
                line = line.rstrip("\n")
                for ip in ipaddress.IPv4Network(line):
                    if str(ip) not in ip_list:
                        ip_list.append(str(ip))
            fr.close()
        with open("C:\\Users\\Admin\\Documents\\crtsh\\Bank\\IP_address\\{}_ip_list.txt".format(asn), "w") as fw:
            for ip in ip_list:
                fw.write(ip + "\n")
            fw.close()
        ip_list.clear()

'''Tìm kiếm DNS từ danh sách IP'''
def reverse_dns_lookup(ip_address):
    try:
        resolver = dns.resolver.Resolver()
        ip = ip_address.split(".")
        ip_reverse = "{}.{}.{}.{}".format(ip[3], ip[2], ip[1], ip[0])
        ptr_record = "{}.in-addr.arpa".format(ip_reverse)
        answers = resolver.resolve(ptr_record, "PTR")

        if answers:
            return answers[0].to_text().rstrip(".")
        else:
            return None
    except dns.exception.DNSException as e:
        return None

def get_bank_list():
    asn_bank_list = []
    with open("C:\\Users\\Admin\\Documents\\crtsh\\asn_bank_vn.txt", "r") as file:
        lines = file.readlines()
        for line in lines:
            asn_bank_list.append(line.rstrip("\n"))
    return asn_bank_list

def get_dns(ip: str):
    hostname = reverse_dns_lookup(ip)
    if hostname:
        # print("{}\t{}".format(ip, hostname))
        return ip, hostname

def get_dns_list():
    asn_bank_list = get_bank_list()
    for asn in asn_bank_list:
        ip_list = []
        with open("C:\\Users\\Admin\\Documents\\crtsh\\Bank\\IP_address\\{}_ip_list.txt".format(asn), "r") as fr:
            lines = fr.readlines()
            for line in lines:
                ip_list.append(line.rstrip("\n"))
        with ThreadPoolExecutor(max_workers=16) as exec:
            results = list(exec.map(get_dns, ip_list))
        ip_list.clear()
        with open("C:\\Users\\Admin\\Documents\\crtsh\\Bank\\IP_address\\Hostname\\{}_hostname.txt".format(asn), "w") as fw:
            for res in results:
                if res:
                    fw.write("{}\t{}\n".format(res[0], res[1]))