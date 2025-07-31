nodejs code to scraping this. 


-categories req

fetch("https://webcommerce-gw.alfagift.id/v2/categories", {
  "headers": {
    "accept": "application/json",
    "accept-language": "id",
    "devicemodel": "chrome",
    "devicetype": "Web",
    "fingerprint": "hNvsXdRTVhrqH5gGgHkI8OnvtKOGC8E/vIk1u9NwkKyV1i1yorHlQQr52UMqtait",
    "latitude": "0",
    "longitude": "0",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "trxid": "8582286277",
    "Referer": "https://alfagift.id/"
  },
  "body": null,
  "method": "GET"
});

-categories res
{
    "categories": [
        {
            "categoryId": "5b85712ca3834cdebbbc4363",
            "categoryLevel": 0,
            "categoryName": "Kebutuhan Dapur",
            "categoryNameEng": "",
            "categoryImageFileName": "https://cdn.alfagift.id/media/bo/product/ama/category/pm_category_190116_Qqxu.png",
            "parentId": "",
            "metaTitle": "",
            "metaKeyword": "",
            "metaDescription": "",
            "seoText": "",
            "subCategories": [
                {
                    "categoryId": "5b857288a3834cdebbbc4389",
                    "categoryLevel": 1,
                    "categoryName": "Perlengkapan Dapur & Ruang Makan",
                    "categoryNameEng": "",
                    "categoryImageFileName": "https://cdn.alfagift.id/media/bo/product/ama/category/pm_category_231129_ZRkV.png",
                    "parentId": "5b85712ca3834cdebbbc4363",
                    "metaTitle": "",
                    "metaKeyword": "",
                    "metaDescription": "",
                    "seoText": "",
                    "subCategories": null
                },
                ...
            }
        ]
    }

loop thorugh categories > subCategories, get subCategory.categoryId

-products req

fetch("https://webcommerce-gw.alfagift.id/v2/products/category/5b87bc729de3335b80cb353e?sortDirection=asc&start=0&limit=60", {
  "headers": {
    "accept": "application/json",
    "accept-language": "id",
    "devicemodel": "chrome",
    "devicetype": "Web",
    "fingerprint": "hNvsXdRTVhrqH5gGgHkI8OnvtKOGC8E/vIk1u9NwkKyV1i1yorHlQQr52UMqtait",
    "latitude": "0",
    "longitude": "0",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "trxid": "7111114118",
    "Referer": "https://alfagift.id/"
  },
  "body": null,
  "method": "GET"
});

-products res
{
    "totalData": 170,
    "totalPage": 2,
    "pageSize": 60,
    "currentPage": 1,
    "currentCategoryId": "5b87bc729de3335b80cb353e",
    "currentCategoryName": "Makanan Bayi & Anak",
    "currentCategoryParentId": "5b85712ca3834cdebbbc4367",
    "currentCategoryParentName": "Kebutuhan Ibu & Anak",
    "metaTitle": "",
    "metaDescription": "",
    "seoText": "",
    "linkTitle": "",
    "products": [
        {
            "productId": "813164",
            "productName": "SUN Biskuit Marie Keju Anak 80 g",
            "image": "https://c.alfagift.id/product/1/1_A8131640002167_20241203145224020_base.jpg",
            "sku": "A8131640002167",
            "plu": "444003",
            "ageRestriction": 0,


loop and to list products and export to json. parameterize pagination from "totalPage" 