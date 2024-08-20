import requests
import dns.resolver
import time
from statistics import mean
from collections import defaultdict

def check_dns_load_balancer(domain, num_lookups=20):
    """Check for DNS-based load balancing by performing multiple DNS lookups."""
    resolver = dns.resolver.Resolver()
    ip_addresses = []
    
    for i in range(num_lookups):
        try:
            answers = resolver.resolve(domain, 'A')
            for rdata in answers:
                ip = rdata.to_text()
                if ip not in ip_addresses:
                    ip_addresses.append(ip)
                print(f"DNS Lookup {i+1}: {ip}")
            time.sleep(0.5)  # Adding a small delay between lookups to avoid flooding DNS servers
        except dns.resolver.NoAnswer:
            print("No DNS record found.")
        except dns.resolver.NXDOMAIN:
            print("Domain does not exist.")
        except Exception as e:
            print(f"DNS Lookup error: {e}")

    return ip_addresses

def check_http_load_balancer(url, num_requests=20):
    """Check for HTTP load balancing by sending multiple requests and analyzing headers and response times."""
    servers = []
    response_times = []
    headers_dict = defaultdict(int)
    additional_headers = defaultdict(lambda: defaultdict(int))

    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.get(url)
            response_time = time.time() - start_time
            
            server = response.headers.get('Server', 'Unknown')
            x_forwarded_for = response.headers.get('X-Forwarded-For')
            via = response.headers.get('Via')
            x_cache = response.headers.get('X-Cache')
            set_cookie = response.headers.get('Set-Cookie')
            
            headers_dict[server] += 1
            response_times.append(response_time)
            
            # Store additional headers for deeper analysis
            additional_headers['X-Forwarded-For'][x_forwarded_for] += 1
            additional_headers['Via'][via] += 1
            additional_headers['X-Cache'][x_cache] += 1
            additional_headers['Set-Cookie'][set_cookie] += 1
            
            print(f"Request {i+1}: Server: {server}, X-Forwarded-For: {x_forwarded_for}, Via: {via}, X-Cache: {x_cache}, Set-Cookie: {set_cookie}, Response Time: {response_time:.4f} sec")
            servers.append(server)
            time.sleep(0.5)  # Adding a small delay between requests to simulate real user activity

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to the URL: {e}")
            return [], [], {}

    return servers, response_times, headers_dict, additional_headers

def main():
    url = input("Enter the URL to check for load balancing (e.g., http://example.com): ").strip()
    domain = url.split("//")[-1].split("/")[0]

    print("\nChecking DNS-based load balancing...")
    dns_ips = check_dns_load_balancer(domain)
    if len(dns_ips) > 1:
        print("DNS-based load balancer detected! Multiple IP addresses were found:")
        print("\n".join(dns_ips))
    else:
        print("No DNS-based load balancer detected based on DNS lookups.")

    print("\nChecking HTTP-based load balancing...")
    servers, response_times, headers_dict, additional_headers = check_http_load_balancer(url)
    
    # Server header analysis
    if len(set(servers)) > 1:
        print("HTTP-based load balancer detected! Different Server headers were returned:")
        print("\n".join(set(servers)))
    else:
        print("No HTTP-based load balancer detected based on Server headers.")

    if headers_dict:
        print("\nServer Header Analysis:")
        for server, count in headers_dict.items():
            print(f"{server}: {count} times")

    # Response time analysis
    if response_times:
        avg_time = mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"\nResponse Time Analysis: Average: {avg_time:.4f} sec, Max: {max_time:.4f} sec, Min: {min_time:.4f} sec")
        if max_time - min_time > 0.5:  # Adjust threshold as needed
            print("Significant variation in response times detected, which may indicate load balancing.")

    # Additional header analysis
    print("\nAdditional Header Analysis:")
    for header, values in additional_headers.items():
        if len(values) > 1:
            print(f"\n{header} Header Variations:")
            for value, count in values.items():
                print(f"  {value}: {count} times")
        else:
            print(f"\nNo significant variations detected in {header} header.")

if __name__ == "__main__":
    main()
