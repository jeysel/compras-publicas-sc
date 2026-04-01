select *, 
    lpad(ano_assinatura::text, 4, '0') as ano_str
from marts.fct_contratos