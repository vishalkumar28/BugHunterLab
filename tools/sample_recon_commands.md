# Recon Command Starters

```bash
subfinder -d example.com -silent
amass enum -passive -d example.com
httpx -l subdomains.txt -tech-detect -title -status-code
nmap -sV -Pn example.com
ffuf -u https://app.example.com/FUZZ -w wordlists/common.txt
nuclei -l live_hosts.txt -severity low,medium,high,critical
sqlmap -u "https://api.example.com/users?id=1" --batch
```