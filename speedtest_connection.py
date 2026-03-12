import speedtest


def run_speedtest():
    s = speedtest.Speedtest()

    # Optional: get specific servers (empty list means all available)
    s.get_servers([])

    # Find the best server based on ping
    best = s.get_best_server()
    print(f"Best server: {best['host']} located in {best['name']}, {best['country']}")

    print("Testing download speed...")
    download = s.download() / 1_000_000  # Convert to Mbps

    print("Testing upload speed...")
    upload = s.upload(pre_allocate=False) / 1_000_000  # Convert to Mbps

    ping = s.results.ping

    print(f"\nDownload speed: {download:.2f} Mbps")
    print(f"Upload speed: {upload:.2f} Mbps")
    print(f"Ping: {ping:.2f} ms")

    # Optional: share results and get URL
    result_url = s.results.share()
    print(f"Result image: {result_url}")

    return s.results.dict()  # Full results if needed


if __name__ == "__main__":
    run_speedtest()
