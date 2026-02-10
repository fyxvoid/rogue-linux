#!/usr/bin/env python3
"""
Rogue Labs CLI
Premium, Private, Performance-first Lab Manager.
"""
import argparse
import sys
import os

# Ensure we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import manager, auth, client, vpn

def main():
    parser = argparse.ArgumentParser(
        description="Rogue Labs: The Pentesting Singularity.",
        epilog="Hack the Planet. Privately."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list
    parser_list = subparsers.add_parser("list", help="List available labs")
    parser_list.add_argument("--filter", help="Filter by category (web, pwn, re)")

    # Command: install
    parser_install = subparsers.add_parser("install", help="Download and configure a lab")
    parser_install.add_argument("lab_id", help="ID of the lab to install")

    # Command: start
    parser_start = subparsers.add_parser("start", help="Spin up a lab environment")
    parser_start.add_argument("lab_id", help="ID of the lab to start")
    parser_start.add_argument("--provider", default="local", choices=["local", "aws", "azure"], help="Provider (local/aws/azure)")

    # Command: stop
    parser_stop = subparsers.add_parser("stop", help="Stop a running lab")
    parser_stop.add_argument("lab_id", help="ID of the lab to stop")
    parser_stop.add_argument("--provider", default="local", choices=["local", "aws", "azure"], help="Provider (local/aws/azure)")

    # Command: submit
    parser_submit = subparsers.add_parser("submit", help="Submit a captured flag")
    parser_submit.add_argument("flag", help="The flag string (e.g., ROGUE{...})")

    # Command: login
    parser_login = subparsers.add_parser("login", help="Authenticate with Rogue Cloud")
    parser_login.add_argument("token", help="Your API Token")

    # Command: vpn
    parser_vpn = subparsers.add_parser("vpn", help="Manage Network Connectivity")
    vpn_subparsers = parser_vpn.add_subparsers(dest="vpn_command", help="VPN Actions")
    
    vpn_subparsers.add_parser("init", help="Download VPN Configuration")
    vpn_subparsers.add_parser("connect", help="Connect to Rogue Cloud VPN")
    vpn_subparsers.add_parser("status", help="Check connection status")

    args = parser.parse_args()

    if args.command == "list":
        manager.list_labs(args.filter)
    elif args.command == "start":
        manager.start_lab(args.lab_id, args.provider)
    elif args.command == "stop":
        manager.stop_lab(args.lab_id, args.provider)
    elif args.command == "submit":
        client.submit_flag(args.flag)
    elif args.command == "login":
        auth.login(args.token)
    elif args.command == "vpn":
        if args.vpn_command == "init":
            vpn.init_vpn()
        elif args.vpn_command == "connect":
            vpn.connect_vpn()
        elif args.vpn_command == "status":
            vpn.status_vpn()
        else:
            parser_vpn.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
