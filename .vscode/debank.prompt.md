<div class="HeaderInfo_totalAssetInner__HyrdC HeaderInfo_curveEnable__HVRYq">$1,461<div class="HeaderInfo_changeInfo__fJunm"><span class="HeaderInfo_changePercent__0ze+J">+1.56%</span><span class="Tips_tips__r0qbI AssetReportIcon_reportIcon__4QOHU"></span></div></div>

<div class="HeaderInfo_totalAssetInner__HyrdC HeaderInfo_curveEnable__HVRYq">$1,461<div class="HeaderInfo_changeInfo__fJunm"><span class="HeaderInfo_changePercent__0ze+J">+1.39%</span><span class="Tips_tips__r0qbI AssetReportIcon_reportIcon__4QOHU"></span></div></div>

<div class="db-user-tag is-age"><img src="https://assets.debank.com/static/media/age.a02a9578b59e5b75b1b66b56520a954b.svg" alt="" class="db-user-tag-icon">1197 days</div>

<div class="HeaderInfo_userInfoContainer__MTsXc"><div class="HeaderInfo_leftContent__YRAB+"><div class="HeaderInfo_infoItem__Wv-61"><div class="HeaderInfo_title__fBOuq">TVF<span class="Tips_tips__r0qbI"></span></div><div class="HeaderInfo_value__7Nj3p">$16.1K</div></div><a class="HeaderInfo_infoItem__Wv-61" href="/profile/0x1d014371800dd8c97c1fe682ca7b30dafb16ea9a/follower"><div class="HeaderInfo_title__fBOuq">Followers</div><div class="HeaderInfo_value__7Nj3p">2</div></a><a class="HeaderInfo_infoItem__Wv-61" href="/profile/0x1d014371800dd8c97c1fe682ca7b30dafb16ea9a/following"><div class="HeaderInfo_title__fBOuq">Following</div><div class="HeaderInfo_value__7Nj3p">0</div></a><div class="HeaderInfo_infoItem__Wv-61"><div class="HeaderInfo_title__fBOuq">Earnings<span class="Tips_tips__r0qbI"></span></div><div class="HeaderInfo_value__7Nj3p">$0</div></div><button class="Button_button__ufG7+ Button_is_primary__xv+n5 Button_is_ghost__ialgT FollowButton_followBtn__I1dri FollowButton_gradient__w0Fc5 HeaderInfo_followBtn__lNu69" aria-disabled="false"><div class="FollowButton_followBtnInner__XNYJh">Follow</div></button><div class="HeaderInfo_divider__13UBU"></div><div class="HeaderInfo_infoItem__Wv-61"><div class="HeaderInfo_title__fBOuq">Hi offer price<span class="Tips_tips__r0qbI"></span></div><div class="HeaderInfo_value__7Nj3p">$1.00</div></div><div class="HeaderInfo_sayHiBtn__IWO+C">Say Hi</div></div></div>


<div class="Panel_card__1vXt+"><div><div class="table_header__onfbK flex_flexRow__y0UR2 "><div><span>Pool</span></div><div><span>Balance</span></div><div><span>Rewards</span></div><div><span>USD Value</span></div></div><div class="table_content__53NAZ"><div class="table_contentRow__Mi3k5 flex_flexRow__y0UR2 "><div><span><div title="" class="Flex_flex__KFQty Flex_flexRow__jNYOK LabelWithIcon_container__-yKOy"><div class="tokenIcons" style="width: 26px;"><div style="left: 0px;"><img src="https://static.debank.com/image/eth_token/logo_url/0x88909d489678dd17aa6d9609f89b0419bf78fd9a/d20894519040378c045116eb6825c2a9.png" style="width: 20px; height: 20px;"></div></div><div class=""><a class="utils_detailLink__XnB7N" target="_blank" href="/token/eth/0x88909d489678dd17aa6d9609f89b0419bf78fd9a">L3</a></div></div></span></div><div><span><div style="margin-top: 0px;">690.1085 <a class="utils_detailLink__XnB7N" target="_blank" href="/token/eth/0x88909d489678dd17aa6d9609f89b0419bf78fd9a">L3</a> </div></span></div><div><span><div style="margin-top: 0px;">372.0866 <a class="utils_detailLink__XnB7N" target="_blank" href="/token/eth/0x88909d489678dd17aa6d9609f89b0419bf78fd9a">L3</a> ($18.84)</div></span></div><div><span>$53.79</span></div></div> </div></div></div>


---

## new

fix code 

```async function extractProtocols(page) {
  await page.waitForSelector("div[class^='table_contentRow__']", { timeout: 10000 });
  const headerGroups = await page.$$eval(
    "div[class^='table_header__']",
    (headers) =>
      headers.map((header) => {
        const spans = Array.from(header.querySelectorAll("div > span"));
        return spans.map((span) => span.innerText.trim());
      })
  );
  const valueGroups = await page.$$eval(
    "div[class^='table_contentRow__']",
    (rows) =>
      rows.map((row) => {
        const spans = Array.from(row.querySelectorAll("div > span"));
        return spans.map((span) => span.innerText.trim());
      })
  );
  return valueGroups.map((values, index) => {
    const headers = headerGroups[index] || [];
    const obj = {};
    headers.forEach((key, i) => {
      obj[key] = values[i] || null;
    });
    return obj;
  });
}```

to extract these multiple protocols (this not the only one):

```
<div class="Project_project__GCrhx"><div id="_hyperliquid" class="ProjectTitle_projectTitle__yC5VD"><div class="ProjectTitle_projectMeta__2HYAt"><div class="ProjectTitle_projectIcon__yiNo9"><div class="TokenAvatar_iconWithChain__Xph-n" style="width: 20px; height: 20px;"><div style="width: 20px; height: 20px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h table_isAppchain__5nGQM"><img class="db-lazyMedia-img" src="https://static.debank.com/image/project/logo_url/arb_hyperliquid/98dcfcb24e1ec2ab0da74679e0bfa0bb.png" alt=""></div></div></div></div><div class="ProjectTitle_name__x2ZNR"><span class="ProjectTitle_protocolLink__4Yqn3">Hyperliquid</span><a href="https://app.hyperliquid.xyz" target="_blank" rel="noopener noreferrer" class="ProjectTitle_projectSiteUrl__3DvN-"></a></div></div><div class="projectTitle-number">$198</div></div><div class="Panel_container__Vltd1"><div class="Panel_panelHead__p5zwE"><div class="BookMark_container__KX3BL"><div class="BookMark_bookmark__UG5a4">Yield</div></div></div><div class="Panel_card__1vXt+"><div><div class="table_header__onfbK flex_flexRow__y0UR2 "><div><span>&nbsp;</span></div><div><span>Pool</span></div><div><span>Balance</span></div><div><span>USD Value</span></div></div><div class="table_content__53NAZ"><div class="table_contentRow__Mi3k5 flex_flexRow__y0UR2 "><div><span>Main-Account Vaults</span></div><div><span><div title="" class="Flex_flex__KFQty Flex_flexRow__jNYOK LabelWithIcon_container__-yKOy"><div class="tokenIcons" style="width: 26px;"><div style="left: 0px;"><img src="https://static.debank.com/image/eth_token/logo_url/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48/fffcd27b9efff5a86ab942084c05924d.png" style="width: 20px; height: 20px;"></div></div><div class=""><a class="utils_detailLink__XnB7N" target="_blank" href="/token/undefined/cbc85c2463806ead7328a5da06425a2b">USDC</a></div></div></span></div><div><span><div style="margin-top: 0px;">198.4327 <a class="utils_detailLink__XnB7N" target="_blank" href="/token/undefined/cbc85c2463806ead7328a5da06425a2b">USDC</a> </div></span></div><div><span>$198.43</span></div></div> </div></div></div></div></div>
```

---

```
async function extractWallets(page) {
  await page.waitForSelector("div[class*='TokenWallet_table']", { timeout: 10000 });
  return await page.evaluate(() => {
    const table = document.querySelector("div[class*='TokenWallet_table']");
    if (!table) return [];
    const headerEls = table.querySelectorAll("div[class*='db-table-headerItem']");
    const headers = Array.from(headerEls).map((el) => el.innerText.trim());
    const rowEls = table.querySelectorAll("div[class*='db-table-row']");
    return Array.from(rowEls).map((row) => {
      const cells = row.querySelectorAll("div[class*='db-table-cell']");
      const values = Array.from(cells).map((cell, i) => {
        if (i === 0) {
          const tokenLink = cell.querySelector("a");
          return tokenLink?.innerText.trim() || "";
        }
        return cell.innerText.trim();
      });
      const rowObj = {};
      headers.forEach((key, i) => {
        rowObj[key] = values[i] || "";
      });
      return rowObj;
    });
  });
}```

improve code to add chain key which is in href. for example in `href="/token/linea/linea"`. the chain is `linea`


```
<div class="TokenWallet_container__FUGTE"><div class="ProjectTitle_projectTitle__yC5VD TokenWallet_walletProjectTitle__6TZPs" id="Wallet"><div class="ProjectTitle_projectMeta__2HYAt"><div class="ProjectTitle_projectIcon__yiNo9"><img src="https://assets.debank.com/static/media/wallet.c61439f1c1a4e799555efeeb1032fda8.svg" alt=""></div><div class="ProjectTitle_name__x2ZNR">Wallet</div></div><div class="projectTitle-number">$1,166</div></div><div class="Card_card__pSup9 TokenWallet_card__teb0g"><div class="db-table TokenWallet_table__bmN1O"><div class="db-table-main"><div class="db-table-header"><div class="db-table-headerItem" data-idx="0" style="width: 30%;">Token</div><div class="db-table-headerItem" data-idx="1" style="width: 25%;">Price</div><div class="db-table-headerItem" data-idx="2" style="width: 25%;">Amount</div><div class="db-table-headerItem is-right" data-idx="3" style="width: 20%;">USD Value</div></div><div class="db-table-body is-noEndBorder"><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/eth_token/logo_url/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48/fffcd27b9efff5a86ab942084c05924d.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/base/ccc1513e4f390542c4fb2f4b88ce9579.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/base/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913">USDC</a></div></div><div class="db-table-cell" style="width: 25%;">$1.0002</div><div class="db-table-cell" style="width: 25%;">488.2007</div><div class="db-table-cell is-right" style="width: 20%;">$488.30</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/coin/logo_url/eth/6443cdccced33e204d90cb723c632917.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/linea/32d4ff2cf92c766ace975559c232179c.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/linea/linea">ETH</a></div></div><div class="db-table-cell" style="width: 25%;">$3,506.3700</div><div class="db-table-cell" style="width: 25%;">0.1041</div><div class="db-table-cell is-right" style="width: 20%;">$365.01</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/coin/logo_url/eth/6443cdccced33e204d90cb723c632917.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/arb/854f629937ce94bebeb2cd38fb336de7.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/arb/arb">ETH</a></div></div><div class="db-table-cell" style="width: 25%;">$3,505.0500</div><div class="db-table-cell" style="width: 25%;">0.0676</div><div class="db-table-cell is-right" style="width: 20%;">$236.85</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/coin/logo_url/eth/6443cdccced33e204d90cb723c632917.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/base/ccc1513e4f390542c4fb2f4b88ce9579.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/base/base">ETH</a></div></div><div class="db-table-cell" style="width: 25%;">$3,504.6700</div><div class="db-table-cell" style="width: 25%;">0.0155</div><div class="db-table-cell is-right" style="width: 20%;">$54.28</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/coin/logo_url/eth/6443cdccced33e204d90cb723c632917.png" alt=""></div></div></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/eth/eth">ETH</a></div></div><div class="db-table-cell" style="width: 25%;">$3,504.6700</div><div class="db-table-cell" style="width: 25%;">0.0024</div><div class="db-table-cell is-right" style="width: 20%;">$8.28</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/matic_token/logo_url/matic/6f5a6b6f0732a7a235131bd7804d357c.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/matic/52ca152c08831e4765506c9bd75767e8.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/matic/matic">POL</a></div></div><div class="db-table-cell" style="width: 25%;">$0.1972</div><div class="db-table-cell" style="width: 25%;">18.3375</div><div class="db-table-cell is-right" style="width: 20%;">$3.62</div></div></div><div class="db-table-wrappedRow"><div class="db-table-row"><div class="db-table-cell" style="width: 30%;"><div class="TokenWallet_tokenInfo__5PsgW"><div class="TokenAvatar_iconWithChain__Xph-n TokenWallet_tokenIcon__h9Vi9" style="width: 24px; height: 24px;"><div style="width: 24px; height: 24px;"><div class="db-lazyMedia TokenAvatar_icon__p2M2h"><img class="db-lazyMedia-img" src="https://static.debank.com/image/coin/logo_url/eth/6443cdccced33e204d90cb723c632917.png" alt=""></div></div><img class="TokenAvatar_chainLogo__uy+ny TokenWallet_tokenChainIcon__zyi8Q" src="https://static.debank.com/image/chain/logo_url/zora/de39f62c4489a2359d5e1198a8e02ef1.png" alt="" style="width: 12px; height: 12px;"></div><a class="TokenWallet_detailLink__goYJR" target="_blank" href="/token/zora/zora">ETH</a></div></div><div class="db-table-cell" style="width: 25%;">$3,505.6700</div><div class="db-table-cell" style="width: 25%;">0.0008</div><div class="db-table-cell is-right" style="width: 20%;">$2.83</div></div></div></div></div><div class="db-table-sticky-bar"><div class="db-table-scrollbar" style="width: 1168px;"></div></div></div><div class="TokenWallet_showAll__PecCN">Tokens with small balances are not displayed.<span>Show all</span></div></div><div class="db-centerModal-wrap"></div></div>```