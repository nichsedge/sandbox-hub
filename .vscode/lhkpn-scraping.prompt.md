I need a Python script to scrape public LHKPN data from `https://elhkpn.kpk.go.id/`. The website uses dynamic JavaScript loading, CSRF tokens, and various anti-bot measures, including frequent redirects and pop-ups. I would prefer a solution using **`nodriver`** or **`puppeteer`**.

Here is a step-by-step breakdown of the process:

1.  **Initial Navigation and Pop-up Handling:**
    * Navigate to the base URL: `https://elhkpn.kpk.go.id/`.
    * The site will redirect to `https://elhkpn.kpk.go.id/portal/user/login#modal-notice` and display a pop-up. Close this pop-up.
    * It will then redirect again to `https://elhkpn.kpk.go.id/portal/user/login#modal-notice-two` with a second pop-up. Close this pop-up as well.

2.  **Accessing the Search Form:**
    * After closing the pop-ups, navigate to `https://elhkpn.kpk.go.id/portal/user/login#announ`.
    * Locate the search form on this page.

3.  **Performing a Search:**
    * Find the input field with `id="CARI_NAMA"` and the placeholder "Nama/NIK."
    * Enter a politician's name, such as **"prabowo subianto"**, into this field.
    * Click the search button: `<button type="submit" class="btn btn-success"><i class="fa fa-search"></i></button>`.

4.  **Extracting Data from Results:**
    * Once the results table is displayed, the script needs to paginate through all pages. The "Next" button is an `<a>` tag with a structure similar to `<a href="..." data-ci-pagination-page="10">Next ≫</a>`.
    * For each row in the results table, find the `<a>` tag with the class `perbandingan-announcement`.
    * From this `<a>` tag, extract the `data-harta` attribute. This attribute contains the URL to the JSON data for that entry.
    * Make an HTTP request to this `data-harta` URL to collect the JSON data.

The final output should be a collection of all JSON objects retrieved from the `data-harta` URLs for the specified search query, across all pages of the results.