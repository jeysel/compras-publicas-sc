from app.masking import classify_id_contratado, mask_id_contratado


def test_classify_cpf_mascarado_na_fonte():
    assert classify_id_contratado("***.006.069-**") == "cpf_mascarado_na_fonte"


def test_classify_cnpj():
    assert classify_id_contratado("00.000.000/0001-91") == "cnpj"


def test_classify_nao_identificado():
    assert classify_id_contratado("9876544") == "nao_identificado"
    assert classify_id_contratado("505") == "nao_identificado"


def test_mask_is_pass_through_for_cpf_ja_mascarado():
    assert mask_id_contratado("***.006.069-**") == "***.006.069-**"


def test_mask_is_pass_through_for_cnpj():
    assert mask_id_contratado("00.000.000/0001-91") == "00.000.000/0001-91"


def test_mask_is_pass_through_for_malformado():
    assert mask_id_contratado("9876544") == "9876544"
