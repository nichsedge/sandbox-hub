with
    cte_0 as (
        select
            pname as product_name,
            case
                kname
                when 'Keyboard'
                then 'keymouse'
                when 'Processor'
                then 'proc'
                when 'Hard Drive'
                then 'storage'
                when 'RAM'
                then 'memory'
                when 'SSD'
                then 'storage'
                else kname
            end as category,
            json_extract_array(pprcz)[safe_offset(0)] as price,
            date(date_trunc(date(inserted_at), week)) as inserted_at,
            'enterkomputer' as source
        from {{ source("dezoomcamp", "enterkomputer_raw") }}
    )
select
    product_name,
    lower(category) as category,
    safe_cast(price as integer) as price,
    inserted_at,
    source
from
    cte_0

    -- lcd
    -- psu
    -- vga
    -- proc
    -- audio
    -- tinta
    -- casing
    -- cooler
    -- gadget
    -- memory
    -- office
    -- server
    -- printer
    -- storage
    -- keymouse
    -- notebook
    -- software
    -- aksesoris
    -- pcbranded
    -- projector
    -- networking
    -- rackserver
    -- motherboard
    -- partnotebook
    -- mcardflashdisk
    -- ups-stabilizer
    -- KNAME
    -- PSU
    -- Casing
    -- LCD
    -- Keyboard
    -- Processor
    -- Hard Drive
    -- Cooler
    -- RAM
    -- SSD
    -- VGA
    -- Motherboard
    
