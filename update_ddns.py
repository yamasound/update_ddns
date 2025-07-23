#!/usr/bin/env python3
#
# update_ddns.py
#
# required: sudo apt install python3-dns

import dns.resolver, re, socket, sys, urllib.request, yaml

def read_params():
    # YAMLファイルの読み込み
    with open('YOUR_PARAMS') as file:
        d = yaml.safe_load(file)
    return d['domain'], d['host'], d['pw']

def get_current_ip():
    # 現在使用中のIPの取得
    current_ip = None
    req = urllib.request.Request(url='http://inet-ip.info/ip', method='GET')
    with urllib.request.urlopen(req) as f:
        if f.status == 200:
            current_ip = f.read().decode('utf-8').strip()

    if current_ip is None:
        req = urllib.request.Request(url='http://globalip.me', method='GET')
        req.add_header('User-Agent', 'curl')
        with urllib.request.urlopen(req) as f:
            if f.status == 200:
                current_ip = f.read().decode('utf-8').strip()
    
    if current_ip is None:
        print('現在使用中のIPの取得に失敗しました', file=sys.stderr)
        exit(1)

    print(f'現在使用中のIPは{current_ip}です')
    return current_ip

def check_registered_ipaddress(domain, host, current_ip):
    # DDNSに登録してあるIPとの比較
    
    def get_fqdn(domain, host):
        # FQDNの取得
        if host == '':
            fqdn = domain
        else:
            fqdn = f'{host}.' + domain
        return fqdn
    
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [
        socket.gethostbyname('ns1.value-domain.com'),
        socket.gethostbyname('ns2.value-domain.com'),
    ]
    address_list = resolver.resolve(get_fqdn(domain, host), 'A')
    for ipaddress in address_list:
        if current_ip == str(ipaddress):
            print(f'DDNSに登録してあるIPの更新は不要です')
            exit(0)
    print(f'DDNSに登録してあるIP({ipaddress})の更新が必要です')
            
def update_ddns(domain, host, pw, current_ip):
    # DDNSに登録してあるIPの更新
    
    d_status = { '0': '更新に成功',
                 '1': '不正なリクエスト',
                 '2': '不正なドメインとパスワード',
                 '3': '不正なIP',
                 '4': 'パスワードが一致しない',
                 '5': 'データベースサーバーが混雑している',
                 '8': '更新対象のレコードがない',
                 '9': 'その他のエラー',
                 '503': '連続アクセス等の過負荷エラー'
                }
    def print_error_and_exit(results, message):
        # エラーの表示と終了
        print(f'IPの更新に失敗しました．{results} 理由:{message}',
              file=sys.stderr)
        exit(1)

    print(f'DDNSに登録してあるIPを更新します')
    post_data = f'd={domain}&h={host}&p={pw}&i={current_ip}'.encode('utf-8')
    req = urllib.request.Request(
        url='https://dyn.value-domain.com/cgi-bin/dyn.fcg',
        data=post_data, method='POST')
    with urllib.request.urlopen(req) as f:
        if f.status == 200:
            message = ''
            results = f.read().decode('utf-8').strip()
            match = re.match(r'status\s*=\s*(\d+)', results, re.IGNORECASE)
            if match is not None:
                code = match.group(1)
                if code in d_status:
                    message = d_status[code]
                if code == '0':
                    print(f'IPを更新しました')
                else:
                    print_error_and_exit(results, message)
            else:
                print_error_and_exit(results, message)
        else:
            print(f'IPの更新に失敗しました．接続ステータス:{f.status}',
                  file=sys.stderr)
            exit(1)

def main():
    domain, host, pw = read_params()
    current_ip = get_current_ip()
    check_registered_ipaddress(domain, host, current_ip)
    update_ddns(domain, host, pw, current_ip)

if __name__ == '__main__':
    main()
