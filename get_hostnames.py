import requests
import csv
import dns.resolver
import dns.exception
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from time import sleep
from random import randint

'''Lấy số lượng ASN ở Việt Nam'''
def get_asn_amount():
    url = "https://ipinfo.io/countries/vn"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
        }
    res = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    rows = soup.find_all("tr", class_="even:bg-charcoal-blue-03 px-6")[0]
    data = rows.find("a")
    # print(data.text.strip())
    return data.text.strip()

'''Xuất danh sách các ASN ở Việt Nam'''
def export_asn_list_vn():
    url = "https://ipinfo.io/api/data/asns?country=vn&amount=20&page={}"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
        }
    amount = int(get_asn_amount())
    with open("DS_ASN_VN.csv", "w", newline="") as file:
        writer = csv.writer(file)
        header = ["ASN","Name", "Country", "Number of IPs", "Type"]
        writer.writerow(header)
        for i in range(int(amount/20)+1):
            # sleep(randint(1, 5))
            res = requests.get(url=url.format(i), headers=headers)
            data = res.json()
            if isinstance(data, list):
                for item in data:
                    writer.writerow(list(item.values()))

'''Cập nhật danh sách ASN ở Việt Nam ra file csv'''
def update_asn_list():
    amount = int(get_asn_amount())
    with open("DS_ASN_VN.csv", "r") as file:
        reader = csv.reader(file)
        cnt = sum(1 for _ in reader)
    if cnt < amount:
        with open("DS_ASN_VN.csv", "w", newline="") as file:
            writer = csv.writer(file)
            header = ["ASN","Name", "Country", "Number of IPs", "Type"]
            writer.writerow(header)
            url = "https://ipinfo.io/api/data/asns?country=vn&amount=20&page={}"
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
                }
            for i in range(int(amount/20)+1):
                # sleep(randint(1, 5))
                res = requests.get(url=url.format(i), headers=headers)
                data = res.json()
                if isinstance(data, list):
                    for item in data:
                        writer.writerow(list(item.values()))

'''Xuất danh sách ASN của các ngân hàng ở Việt Nam ra file txt'''
def export_asn_bank_list():
    asn_bank_list = []
    with open("DS_ASN_VN.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0]=="asn": continue
            if row[2] != "0" and ("bank" in row[1] or "Bank" in row[1] or "BANK" in row[1]):
                asn_bank_list.append(row[0])

    with open("asn_bank_vn.txt", "w") as file:
        for i in asn_bank_list:
            file.write(i + "\n")

'''Xuất danh sách ASN của Việt Nam từ csv ra txt'''
def export_asn_vn_list():
    asn_list = []
    with open("DS_ASN_VN.csv", "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0]=="asn": continue
            else:
                asn_list.append(row[0])

    with open("asn_vn_list.txt", "w") as file:
        for i in asn_list:
            file.write(i + "\n")

'''Lấy danh sách'''
def get_list(list_file):
    list = []
    with open(list_file, "r") as file:
        lines = file.readlines()
        for line in lines:
            list.append(line.rstrip("\n"))
    return list

'''Lấy danh sách IP block của ASN'''
def get_ip_block_list():
    asn_bank_list = get_list("asn_bank_vn.txt")
    # asn_list = get_list("asn_vn_list.txt")
    for asn in asn_bank_list:
        # print(asn)
        # sleep(randint(1, 5))
        url = "https://ipinfo.io/{}"
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
            }
        res = requests.get(url=url.format(asn), headers=headers)
        soup = BeautifulSoup(res.text, "lxml")
        tables = soup.find_all("table", class_="table table-bordered table-md table-details")
        datas = tables[0].find_all("a")
        with open("Bank/{}_ip_blocks.txt".format(asn), "w") as file:
            for data in datas:
                file.write(data.text.strip() + "\n")

'''Tạo danh sách IP từ danh sách IP Blocks'''
def create_ip_list():
    ip_list = []
    asn_bank_list = get_list("asn_bank_vn.txt")
    # asn_list = get_list("asn_vn_list.txt")
    for asn in asn_bank_list:
        with open("Bank/{}_ip_blocks.txt".format(asn), "r") as fr:
            lines = fr.readlines()
            for line in lines:
                line = line.rstrip("\n")
                for ip in ipaddress.IPv4Network(line):
                    if str(ip) not in ip_list:
                        ip_list.append(str(ip))
            fr.close()
        with open("Bank/IP_address/{}_ip_list.txt".format(asn), "w") as fw:
            for ip in ip_list:
                fw.write(ip + "\n")
            fw.close()
        ip_list.clear()

'''Tìm kiếm DNS từ IP'''
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

def get_dns(ip: str):
    hostname = reverse_dns_lookup(ip)
    if hostname:
        # print("{}\t{}".format(ip, hostname))
        return ip, hostname

'''Lấy danh sách DNS của 1 ASN'''
def get_dns_list():
    asn_bank_list = get_list("asn_bank_vn.txt")
    # asn_list = get_list("asn_vn_list.txt")
    for asn in asn_bank_list:
        ip_list = []
        with open("Bank/IP_address/{}_ip_list.txt".format(asn), "r") as fr:
            lines = fr.readlines()
            for line in lines:
                ip_list.append(line.rstrip("\n"))
        with ThreadPoolExecutor(max_workers=16) as exec:
            results = list(exec.map(get_dns, ip_list))
        ip_list.clear()
        with open("Bank/IP_address/Hostname/{}_hostname.txt".format(asn), "w") as fw:
            for res in results:
                if res:
                    fw.write("{}\t{}\n".format(res[0], res[1]))
