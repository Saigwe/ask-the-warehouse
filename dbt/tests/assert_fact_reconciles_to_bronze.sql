-- The fact keeps every line and every cent of the raw load, and obligations + de-obligations = net.
with b as (select count(*) as n, sum(amount_usd) as net from {{ source('bronze', 'spend_lines') }}),
f as (select count(*) as n, sum(amount_usd) as net, sum(obligation_usd + deobligation_usd) as split from {{ ref('fct_spend_lines') }})
select * from b, f
where b.n <> f.n or abs(b.net - f.net) > 0.01 or abs(f.split - f.net) > 0.01
