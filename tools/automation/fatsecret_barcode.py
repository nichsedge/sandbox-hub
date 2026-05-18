# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.31.0",
#     "python-dotenv>=1.0.1",
#     "rich>=13.7.0",
# ]
# ///

import os
import sys
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

# Use Rich for beautiful terminal outputs
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm

console = Console()

TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
API_BASE_URL = "https://platform.fatsecret.com/rest"


def get_env_paths():
    """Returns possible locations for the .env file in order of priority."""
    paths = [
        Path.cwd() / ".env",  # Current working directory
        Path(__file__).resolve().parents[2] / ".env",  # Root workspace directory
    ]
    return list(dict.fromkeys(paths))  # Remove duplicates while preserving order


def load_credentials(env_file_path=None):
    """Loads Client ID and Secret from CLI, env, or prompts the user."""
    # 1. Try loading from specified or standard .env files
    if env_file_path:
        load_dotenv(dotenv_path=env_file_path)
    else:
        for path in get_env_paths():
            if path.exists():
                load_dotenv(dotenv_path=path)
                break

    client_id = os.getenv("FATSECRET_CLIENT_ID")
    client_secret = os.getenv("FATSECRET_CLIENT_SECRET")

    return client_id, client_secret


def save_credentials_to_env(client_id, client_secret):
    """Appends or updates credentials in the primary .env file."""
    # Determine the target .env file (prefer root workspace, default to cwd)
    env_paths = get_env_paths()
    target_env = env_paths[-1]  # Root workspace is usually the last one (parent parent parent)

    lines = []
    if target_env.exists():
        with open(target_env, "r", encoding="utf-8") as f:
            lines = f.readlines()

    id_found = False
    secret_found = False

    new_lines = []
    for line in lines:
        if line.startswith("FATSECRET_CLIENT_ID="):
            new_lines.append(f"FATSECRET_CLIENT_ID={client_id}\n")
            id_found = True
        elif line.startswith("FATSECRET_CLIENT_SECRET="):
            new_lines.append(f"FATSECRET_CLIENT_SECRET={client_secret}\n")
            secret_found = True
        else:
            new_lines.append(line)

    if not id_found:
        # Ensure newline before adding if file has content
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"FATSECRET_CLIENT_ID={client_id}\n")
    if not secret_found:
        new_lines.append(f"FATSECRET_CLIENT_SECRET={client_secret}\n")

    with open(target_env, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    console.print(f"[bold green]✓ Saved credentials to {target_env.name} ({target_env})[/bold green]")


def get_access_token(client_id, client_secret):
    """Obtains OAuth 2.0 access token from FatSecret."""
    # Try requesting with both 'basic' and 'barcode' scopes
    payloads = [
        {
            "grant_type": "client_credentials",
            "scope": "basic barcode"
        },
        {
            "grant_type": "client_credentials"  # fallback to let it auto-assign
        }
    ]

    last_error = None
    for payload in payloads:
        try:
            response = requests.post(
                TOKEN_URL,
                data=payload,
                auth=(client_id, client_secret),
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    return data["access_token"]
            
            # Save error info for debugging if needed
            try:
                err_data = response.json()
                last_error = err_data.get("error_description", err_data.get("error", response.text))
            except Exception:
                last_error = f"HTTP {response.status_code}: {response.text}"

        except requests.RequestException as e:
            last_error = str(e)

    # If all token requests failed
    console.print(f"\n[bold red]✗ Authentication Failed![/bold red]")
    console.print(f"[red]Details: {last_error}[/red]\n")
    console.print("[yellow]Troubleshooting tips:[/yellow]")
    console.print("1. Double check your Client ID and Client Secret.")
    console.print("2. [bold]CRITICAL:[/bold] FatSecret requires IP whitelisting for OAuth tokens.")
    console.print("   Please whitelist your current public IP address in the FatSecret Developer Portal:")
    console.print("   [link=https://platform.fatsecret.com/]https://platform.fatsecret.com/[/link] -> Your App -> Edit -> IP Address Whitelist\n")
    sys.exit(1)


def clean_and_pad_barcode(barcode_str):
    """Normalizes and pads barcode to a 13-digit GTIN-13 string."""
    cleaned = "".join(c for c in barcode_str if c.isdigit())
    if not cleaned:
        console.print(f"[bold red]✗ Invalid barcode: '{barcode_str}' contains no digits.[/bold red]")
        sys.exit(1)

    if len(cleaned) < 13:
        padded = cleaned.zfill(13)
        console.print(f"[yellow]ℹ Barcode '{cleaned}' is less than 13 digits. Padded to GTIN-13: '{padded}'[/yellow]")
        return padded
    elif len(cleaned) > 13:
        console.print(f"[yellow]⚠ Barcode '{cleaned}' is longer than 13 digits. Using the raw digits.[/yellow]")
        return cleaned

    return cleaned


def lookup_barcode_v2(barcode, access_token):
    """Attempts to use the GET rest/food/barcode/find-by-id/v2 endpoint (returns food details directly)."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "barcode": barcode,
        "format": "json"
    }

    url = f"{API_BASE_URL}/food/barcode/find-by-id/v2"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        res_json = response.json()
        if "error" in res_json:
            err = res_json["error"]
            code = err.get("code")
            # If food not found, return that explicitly
            if code == 211:
                return {"not_found": True}, None
            # Return error description for other errors
            return None, err.get("message", "Unknown API error")

        food_data = None
        if "food" in res_json and isinstance(res_json["food"], dict):
            food_data = res_json["food"]
        elif isinstance(res_json, dict) and "servings" in res_json:
            food_data = res_json

        if food_data:
            if "servings" in food_data:
                return food_data, None
            
            # Defensive food_id retrieval
            food_id = food_data.get("food_id")
            if isinstance(food_id, dict):
                food_id = food_id.get("value", food_id.get("food_id"))
            if food_id:
                return {"food_id": str(food_id)}, None

        # Defensive fallback if food_id is directly at the root
        food_id_root = res_json.get("food_id")
        if food_id_root:
            if isinstance(food_id_root, dict):
                food_id_root = food_id_root.get("value", food_id_root.get("food_id"))
            return {"food_id": str(food_id_root)}, None

        return None, "Unexpected JSON response structure"

    except requests.RequestException as e:
        return None, str(e)


def lookup_barcode_v1(barcode, access_token):
    """Uses the GET rest/food/barcode/find-by-id endpoint to obtain the food_id."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "barcode": barcode,
        "format": "json"
    }

    url = f"{API_BASE_URL}/food/barcode/find-by-id"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        res_json = response.json()
        if "error" in res_json:
            err = res_json["error"]
            if err.get("code") == 211:
                return {"not_found": True}, None
            return None, err.get("message", "Unknown API error")

        # Defensive food ID retrieval
        food_id = None
        if "food_id" in res_json:
            food_id = res_json["food_id"]
        elif "food" in res_json and isinstance(res_json["food"], dict):
            food_id = res_json["food"].get("food_id")

        if food_id:
            if isinstance(food_id, dict):
                # Handles both {"value": "..."} and nested {"food_id": "..."}
                actual_id = food_id.get("value", food_id.get("food_id"))
                if actual_id:
                    return str(actual_id), None
            else:
                return str(food_id), None

        return None, "No food_id found in response"

    except requests.RequestException as e:
        return None, str(e)


def get_food_details(food_id, access_token):
    """Retrieves full food details using GET rest/food/v5."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "food_id": food_id,
        "format": "json"
    }

    url = f"{API_BASE_URL}/food/v5"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        res_json = response.json()
        if "error" in res_json:
            return None, res_json["error"].get("message", "Unknown food.get error")

        if "food" in res_json:
            return res_json["food"], None

        return None, "No food element in response"

    except requests.RequestException as e:
        return None, str(e)


def display_nutrition_info(food_data):
    """Outputs the food details and nutrition table beautifully."""
    name = food_data.get("food_name", "Unknown Food")
    brand = food_data.get("brand_name", "Generic/Unbranded")
    food_type = food_data.get("food_type", "N/A")
    url = food_data.get("food_url", "N/A")
    food_id = food_data.get("food_id", "N/A")

    # Header Panel
    header_text = Text()
    header_text.append(f"🍎 {name}\n", style="bold yellow unicode")
    header_text.append(f"Brand: ", style="bold cyan")
    header_text.append(f"{brand} | ", style="cyan")
    header_text.append(f"Type: ", style="bold green")
    header_text.append(f"{food_type} | ", style="green")
    header_text.append(f"Food ID: ", style="bold magenta")
    header_text.append(f"{food_id}\n", style="magenta")
    if url != "N/A":
        header_text.append(f"Link: ", style="bold blue")
        header_text.append(f"{url}", style="blue underline")

    console.print()
    console.print(Panel(header_text, title="[bold white]Product Details[/bold white]", border_style="bold green"))

    # Servings/Nutrition Table
    servings_wrapper = food_data.get("servings", {})
    serving_raw = servings_wrapper.get("serving", [])

    # Normalize single serving dict to list
    if isinstance(serving_raw, dict):
        servings = [serving_raw]
    else:
        servings = serving_raw

    if not servings:
        console.print("[yellow]⚠ No serving or nutritional data available for this food item.[/yellow]")
        return

    table = Table(
        title=f"[bold green]Nutritional Content per Serving Size[/bold green]",
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )

    # Core Columns
    table.add_column("Serving Description", style="bold white", width=25)
    table.add_column("Weight / Vol", justify="right", style="dim green")
    table.add_column("Calories", justify="right", style="bold yellow")
    table.add_column("Carbs (g)", justify="right", style="red")
    table.add_column("Fat (g)", justify="right", style="magenta")
    table.add_column("Protein (g)", justify="right", style="green")
    table.add_column("Sugar (g)", justify="right", style="red dim")
    table.add_column("Fiber (g)", justify="right", style="green dim")
    table.add_column("Sodium (mg)", justify="right", style="blue dim")

    for s in servings:
        # Metric Amount
        amt = s.get("metric_serving_amount")
        unit = s.get("metric_serving_unit", "")
        weight_str = f"{float(amt):.1f} {unit}" if amt is not None and amt != "" else "N/A"

        # Values (standardize nulls/empty strings to N/A)
        calories = s.get("calories", "N/A")
        carbs = s.get("carbohydrate", "N/A")
        fat = s.get("fat", "N/A")
        protein = s.get("protein", "N/A")
        sugar = s.get("sugar", "N/A")
        fiber = s.get("fiber", "N/A")
        sodium = s.get("sodium", "N/A")

        table.add_row(
            s.get("serving_description", "Standard Serving"),
            weight_str,
            f"{calories} kcal" if calories != "N/A" else "N/A",
            carbs,
            fat,
            protein,
            sugar,
            fiber,
            sodium
        )

    console.print(table)
    console.print()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch detailed nutrition data from FatSecret API based on product barcode."
    )
    parser.add_argument(
        "barcode",
        nargs="?",
        help="The barcode digits of the food product (padded to GTIN-13 automatically)."
    )
    parser.add_argument(
        "--client-id",
        help="FatSecret Client ID/Key (takes precedence over .env)."
    )
    parser.add_argument(
        "--client-secret",
        help="FatSecret Client Secret Key (takes precedence over .env)."
    )
    parser.add_argument(
        "--env-file",
        help="Path to a custom .env file to load credentials from."
    )
    parser.add_argument(
        "--save-env",
        action="store_true",
        help="Save any provided credentials into the .env file."
    )

    args = parser.parse_args()

    # Title Banner
    console.print(Panel(
        "[bold green]🥑 FatSecret Barcode Nutrition Lookup Tool 🥑[/bold green]\n"
        "[dim]Retrieve instant, accurate calorie & macro profiles using GTIN-13 barcodes[/dim]",
        border_style="bold white",
        expand=False
    ))

    # 1. Resolve Credentials
    client_id = args.client_id
    client_secret = args.client_secret

    # If not in args, load from .env file
    env_id, env_secret = load_credentials(args.env_file)
    if not client_id:
        client_id = env_id
    if not client_secret:
        client_secret = env_secret

    # If still missing, prompt the user interactively
    interactive_save = False
    if not client_id or not client_secret:
        console.print("[yellow]⚠ FatSecret API Credentials not found in Environment or .env![/yellow]")
        if not client_id:
            client_id = Prompt.ask("[bold cyan]Enter FatSecret Client ID / Key[/bold cyan]").strip()
        if not client_secret:
            client_secret = Prompt.ask("[bold cyan]Enter FatSecret Client Secret Key[/bold cyan]", password=True).strip()
        
        if client_id and client_secret:
            interactive_save = Confirm.ask("[bold green]? Would you like to save these credentials to your .env file?[/bold green]")

    if not client_id or not client_secret:
        console.print("[bold red]✗ Error: Both Client ID and Client Secret Key are required to run this script.[/bold red]")
        sys.exit(1)

    # Save credentials if requested
    if args.save_env or interactive_save:
        save_credentials_to_env(client_id, client_secret)

    # 2. Get Barcode
    barcode_input = args.barcode
    if not barcode_input:
        barcode_input = Prompt.ask("[bold yellow]🔍 Enter Product Barcode[/bold yellow]").strip()

    if not barcode_input:
        console.print("[bold red]✗ Error: Barcode is required.[/bold red]")
        sys.exit(1)

    barcode = clean_and_pad_barcode(barcode_input)

    # 3. Authenticate and Query
    food_data = None
    with console.status("[bold green]Authenticating with FatSecret Platform...[/bold green]") as status:
        access_token = get_access_token(client_id, client_secret)
        
        status.update("[bold green]Searching barcode via GET /food/barcode/find-by-id/v2...[/bold green]")
        res, err = lookup_barcode_v2(barcode, access_token)
        
        if res:
            if "not_found" in res:
                # Food item explicitly not found
                pass
            elif "food_id" in res and "servings" not in res:
                # v2 only returned food_id, fetch full details via /food/v5
                status.update("[bold green]Fetching details via GET /food/v5...[/bold green]")
                food_data, err = get_food_details(res["food_id"], access_token)
            else:
                # Complete food object returned by v2!
                food_data = res
        else:
            # Fallback to barcode v1 path + food v5 path
            status.update("[bold yellow]v2 GET lookup failed/not permitted. Trying v1 path GET...[/bold yellow]")
            food_id, err_v1 = lookup_barcode_v1(barcode, access_token)
            
            if food_id:
                if isinstance(food_id, dict) and "not_found" in food_id:
                    # Not found
                    pass
                else:
                    status.update("[bold green]Food found! Fetching full nutrient profile via GET /food/v5...[/bold green]")
                    food_data, err = get_food_details(food_id, access_token)
            else:
                err = err_v1

    # 4. Process and Display Results
    if food_data:
        display_nutrition_info(food_data)
    else:
        console.print()
        if err:
            console.print(Panel(
                f"[bold red]✗ API Query Error[/bold red]\n[red]{err}[/red]\n\n"
                "[yellow]Note:[/yellow] If you just registered your credentials, please ensure "
                "your public IP is whitelisted under the developer portal settings.",
                border_style="red"
            ))
        else:
            console.print(Panel(
                f"[bold yellow]⚠ Barcode Not Found[/bold yellow]\n"
                f"No product with barcode [bold]{barcode}[/bold] could be found on the FatSecret Platform.",
                border_style="yellow"
            ))


if __name__ == "__main__":
    main()
