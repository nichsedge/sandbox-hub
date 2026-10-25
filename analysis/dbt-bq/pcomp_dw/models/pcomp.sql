with
    final as (
        select *
        from
            (
                select *
                from {{ ref("enterkomputer") }}
                union all
                select *
                from {{ ref("viraindo") }}
            )
        qualify
            row_number() over (
                partition by product_name, category, price, `source`
                order by inserted_at asc nulls last
            )
            = 1
    )

select
    *,
    case
        -- CPU
        when lower(product_name) like '%amd ryzen 3%'
        then 'AMD Ryzen 3 Series'
        when lower(product_name) like '%amd ryzen 5%'
        then 'AMD Ryzen 5 Series'
        when lower(product_name) like '%amd ryzen 7%'
        then 'AMD Ryzen 7 Series'
        when lower(product_name) like '%amd ryzen 9%'
        then 'AMD Ryzen 9 Series'
        when lower(product_name) like '%intel core i3%'
        then 'Intel Core i3 Series'
        when lower(product_name) like '%intel core i5%'
        then 'Intel Core i5 Series'
        when lower(product_name) like '%intel core i7%'
        then 'Intel Core i7 Series'
        when lower(product_name) like '%intel core i9%'
        then 'Intel Core i9 Series'

        -- RAM
        when lower(product_name) like '%ddr4%' and lower(product_name) like '%2x4gb%'
        then 'DDR4 8GB (2x4GB)'
        when lower(product_name) like '%ddr4%' and lower(product_name) like '%2x8gb%'
        then 'DDR4 16GB (2x8GB)'
        when lower(product_name) like '%ddr4%' and lower(product_name) like '%2x16gb%'
        then 'DDR4 32GB (2x16GB)'
        when lower(product_name) like '%ddr5%' and lower(product_name) like '%2x16gb%'
        then 'DDR5 32GB (2x16GB)'

        -- MONITOR
        -- 23" - 26" Monitors
        when lower(product_name) like '%23" - 26%", 1920 x 1080%'
        then '23-26" FHD (1920x1080)'
        when lower(product_name) like '%23" - 26%", 2560 x 1440%'
        then '23-26" QHD (2560x1440)'

        -- 27" - 30" Monitors
        when lower(product_name) like '%27" - 30%", 1920 x 1080%'
        then '27-30" FHD (1920x1080)'
        when lower(product_name) like '%27" - 30%", 2560 x 1440%'
        then '27-30" QHD (2560x1440)'
        when lower(product_name) like '%27" - 30%", 3840 x 2160%'
        then '27-30" UHD (3840x2160)'
        when lower(product_name) like '%27" - 30%", 2560 x 1080%'
        then '27-30" UltraWide FHD (2560x1080)'

        -- 32"+ Monitors
        when lower(product_name) like '%32"+%, 2560 x 1440%'
        then '32"+ QHD (2560x1440)'
        when lower(product_name) like '%32"+%, 3840 x 2160%'
        then '32"+ UHD (3840x2160)'
        when lower(product_name) like '%32"+%, 2560 x 1080%'
        then '32"+ UltraWide FHD (2560x1080)'
        when lower(product_name) like '%32"+%, 3440 x 1440%'
        then '32"+ UltraWide QHD (3440x1440)'

        -- POWER SUPPLY
        -- < 500W PSUs
        when
            lower(product_name) like '%< 500w%'
            and lower(product_name) like '%80+ bronze%'
        then '< 500W 80+ Bronze'
        when
            lower(product_name) like '%< 500w%'
            and lower(product_name) like '%80+ gold%'
        then '< 500W 80+ Gold'
        when
            lower(product_name) like '%< 500w%'
            and lower(product_name) like '%80+ platinum%'
        then '< 500W 80+ Platinum'

        -- 500W - 799W PSUs
        when
            lower(product_name) like '%500w - 799w%'
            and lower(product_name) like '%80+ bronze%'
        then '500W - 799W 80+ Bronze'
        when
            lower(product_name) like '%500w - 799w%'
            and lower(product_name) like '%80+ gold%'
        then '500W - 799W 80+ Gold'
        when
            lower(product_name) like '%500w - 799w%'
            and lower(product_name) like '%80+ platinum%'
        then '500W - 799W 80+ Platinum'

        -- 800W - 999W PSUs
        when
            lower(product_name) like '%800w - 999w%'
            and lower(product_name) like '%80+ bronze%'
        then '800W - 999W 80+ Bronze'
        when
            lower(product_name) like '%800w - 999w%'
            and lower(product_name) like '%80+ gold%'
        then '800W - 999W 80+ Gold'
        when
            lower(product_name) like '%800w - 999w%'
            and lower(product_name) like '%80+ platinum%'
        then '800W - 999W 80+ Platinum'

        -- 1000W - 1199W PSUs
        when
            lower(product_name) like '%1000w - 1199w%'
            and lower(product_name) like '%80+ bronze%'
        then '1000W - 1199W 80+ Bronze'
        when
            lower(product_name) like '%1000w - 1199w%'
            and lower(product_name) like '%80+ gold%'
        then '1000W - 1199W 80+ Gold'
        when
            lower(product_name) like '%1000w - 1199w%'
            and lower(product_name) like '%80+ platinum%'
        then '1000W - 1199W 80+ Platinum'

        -- 1200W - 1499W PSUs
        when
            lower(product_name) like '%1200w - 1499w%'
            and lower(product_name) like '%80+ gold%'
        then '1200W - 1499W 80+ Gold'
        when
            lower(product_name) like '%1200w - 1499w%'
            and lower(product_name) like '%80+ platinum%'
        then '1200W - 1499W 80+ Platinum'

        -- 1500W - 2000W PSUs
        when
            lower(product_name) like '%1500w - 2000w%'
            and lower(product_name) like '%80+ gold%'
        then '1500W - 2000W 80+ Gold'
        when
            lower(product_name) like '%1500w - 2000w%'
            and lower(product_name) like '%80+ platinum%'
        then '1500W - 2000W 80+ Platinum'

        -- STORAGE
        -- 2.5" SATA Solid State Drives
        when lower(product_name) like '%solid state drive - 2.5" sata 128 gb%'
        then 'SSD 2.5" SATA 128 GB'
        when lower(product_name) like '%solid state drive - 2.5" sata 256 gb%'
        then 'SSD 2.5" SATA 256 GB'
        when lower(product_name) like '%solid state drive - 2.5" sata 512 gb%'
        then 'SSD 2.5" SATA 512 GB'
        when lower(product_name) like '%solid state drive - 2.5" sata 1 tb%'
        then 'SSD 2.5" SATA 1 TB'
        when lower(product_name) like '%solid state drive - 2.5" sata 2 tb%'
        then 'SSD 2.5" SATA 2 TB'

        -- M.2 SATA Solid State Drives
        when lower(product_name) like '%solid state drive - m.2 sata 128 gb%'
        then 'SSD M.2 SATA 128 GB'
        when lower(product_name) like '%solid state drive - m.2 sata 256 gb%'
        then 'SSD M.2 SATA 256 GB'
        when lower(product_name) like '%solid state drive - m.2 sata 512 gb%'
        then 'SSD M.2 SATA 512 GB'
        when lower(product_name) like '%solid state drive - m.2 sata 1 tb%'
        then 'SSD M.2 SATA 1 TB'

        -- M.2 NVMe Solid State Drives
        when lower(product_name) like '%solid state drive - m.2 nvme 128 gb%'
        then 'SSD M.2 NVMe 128 GB'
        when lower(product_name) like '%solid state drive - m.2 nvme 256 gb%'
        then 'SSD M.2 NVMe 256 GB'
        when lower(product_name) like '%solid state drive - m.2 nvme 512 gb%'
        then 'SSD M.2 NVMe 512 GB'
        when lower(product_name) like '%solid state drive - m.2 nvme 1 tb%'
        then 'SSD M.2 NVMe 1 TB'
        when lower(product_name) like '%solid state drive - m.2 nvme 2 tb%'
        then 'SSD M.2 NVMe 2 TB'

        -- 3.5" SATA Hard Drives
        when lower(product_name) like '%hard drive - 3.5" sata 1 tb%'
        then 'HDD 3.5" SATA 1 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 2 tb%'
        then 'HDD 3.5" SATA 2 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 4 tb%'
        then 'HDD 3.5" SATA 4 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 6 tb%'
        then 'HDD 3.5" SATA 6 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 8 tb%'
        then 'HDD 3.5" SATA 8 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 10 tb%'
        then 'HDD 3.5" SATA 10 TB'
        when lower(product_name) like '%hard drive - 3.5" sata 12 tb%'
        then 'HDD 3.5" SATA 12 TB'

        -- VGA
        -- Intel Arc Series
        when lower(product_name) like '%arc a380%'
        then 'Intel Arc A380'
        when lower(product_name) like '%arc a750%'
        then 'Intel Arc A750'
        when lower(product_name) like '%arc a770%'
        then 'Intel Arc A770'

        -- NVIDIA GeForce RTX 30 Series
        when lower(product_name) like '%geforce rtx 3050%'
        then 'NVIDIA GeForce RTX 3050'
        when lower(product_name) like '%geforce rtx 3060 12gb%'
        then 'NVIDIA GeForce RTX 3060 12GB'
        when lower(product_name) like '%geforce rtx 3060 ti lhr%'
        then 'NVIDIA GeForce RTX 3060 Ti LHR'
        when lower(product_name) like '%geforce rtx 3060 ti%'
        then 'NVIDIA GeForce RTX 3060 Ti'
        when lower(product_name) like '%geforce rtx 3070 lhr%'
        then 'NVIDIA GeForce RTX 3070 LHR'
        when lower(product_name) like '%geforce rtx 3070%'
        then 'NVIDIA GeForce RTX 3070'
        when lower(product_name) like '%geforce rtx 3070 ti%'
        then 'NVIDIA GeForce RTX 3070 Ti'
        when lower(product_name) like '%geforce rtx 3080 12gb lhr%'
        then 'NVIDIA GeForce RTX 3080 12GB LHR'
        when lower(product_name) like '%geforce rtx 3080 10gb lhr%'
        then 'NVIDIA GeForce RTX 3080 10GB LHR'
        when lower(product_name) like '%geforce rtx 3080 10gb%'
        then 'NVIDIA GeForce RTX 3080 10GB'
        when lower(product_name) like '%geforce rtx 3080 ti%'
        then 'NVIDIA GeForce RTX 3080 Ti'
        when lower(product_name) like '%geforce rtx 3090 ti%'
        then 'NVIDIA GeForce RTX 3090 Ti'
        when lower(product_name) like '%geforce rtx 3090%'
        then 'NVIDIA GeForce RTX 3090'

        -- NVIDIA GeForce RTX 40 Series
        when lower(product_name) like '%geforce rtx 4070 ti super%'
        then 'NVIDIA GeForce RTX 4070 Ti SUPER'
        when lower(product_name) like '%geforce rtx 4070 super%'
        then 'NVIDIA GeForce RTX 4070 SUPER'
        when lower(product_name) like '%geforce rtx 4070 ti%'
        then 'NVIDIA GeForce RTX 4070 Ti'
        when lower(product_name) like '%geforce rtx 4070%'
        then 'NVIDIA GeForce RTX 4070'
        when lower(product_name) like '%geforce rtx 4080 super%'
        then 'NVIDIA GeForce RTX 4080 SUPER'
        when lower(product_name) like '%geforce rtx 4080%'
        then 'NVIDIA GeForce RTX 4080'
        when lower(product_name) like '%geforce rtx 4090%'
        then 'NVIDIA GeForce RTX 4090'

        -- AMD Radeon RX 6000 Series
        when lower(product_name) like '%radeon rx 6500 xt%'
        then 'AMD Radeon RX 6500 XT'
        when lower(product_name) like '%radeon rx 6600 xt%'
        then 'AMD Radeon RX 6600 XT'
        when lower(product_name) like '%radeon rx 6600%'
        then 'AMD Radeon RX 6600'
        when lower(product_name) like '%radeon rx 6700 xt%'
        then 'AMD Radeon RX 6700 XT'
        when lower(product_name) like '%radeon rx 6800 xt%'
        then 'AMD Radeon RX 6800 XT'
        when lower(product_name) like '%radeon rx 6800%'
        then 'AMD Radeon RX 6800'
        when lower(product_name) like '%radeon rx 6900 xt%'
        then 'AMD Radeon RX 6900 XT'

        -- AMD Radeon RX 7000 Series
        when lower(product_name) like '%radeon rx 7700 xt%'
        then 'AMD Radeon RX 7700 XT'
        when lower(product_name) like '%radeon rx 7800 xt%'
        then 'AMD Radeon RX 7800 XT'
        when lower(product_name) like '%radeon rx 7900 xtx%'
        then 'AMD Radeon RX 7900 XTX'
        when lower(product_name) like '%radeon rx 7900 xt%'
        then 'AMD Radeon RX 7900 XT'
        when lower(product_name) like '%radeon rx 7900 gre%'
        then 'AMD Radeon RX 7900 GRE'

        else 'Other'
    end as product_general_name,
    (
        (
            price - lag(price) over (
                partition by product_name, category, source order by inserted_at
            )
        ) / lag(price) over (
            partition by product_name, category, source order by inserted_at
        )
    )
    * 100 as percentage_change
from final
