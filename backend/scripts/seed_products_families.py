import asyncio
import sys
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, ".")

# DSN local default ou do .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://eventa:*Eventa0101@db:5432/eventa"
)

async def seed_data():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    
    # 1. Definir famílias por PDV
    # Local IDs: Fazendinha = 1, Cantina = 2, Secretaria = 3, Livraria = 4
    families_data = [
        # Fazendinha (1)
        {"nome": "Produtos Coloniais", "local_id": 1},
        {"nome": "Bebidas & Sucos", "local_id": 1},
        {"nome": "Lanches & Salgados", "local_id": 1},
        {"nome": "Lembranças ICM", "local_id": 1},
        # Cantina (2)
        {"nome": "Salgados", "local_id": 2},
        {"nome": "Bebidas", "local_id": 2},
        {"nome": "Doces & Chocolates", "local_id": 2},
        # Secretaria (3)
        {"nome": "Inscrições", "local_id": 3},
        {"nome": "Serviços & Taxas", "local_id": 3},
        # Livraria (4)
        {"nome": "Bíblias & Coletâneas", "local_id": 4},
        {"nome": "Livros & Literatura", "local_id": 4},
    ]

    # 2. Definir novos produtos centrais (inventory_produto)
    new_products = [
        # Cantina
        {"nome": "Pastel de Carne", "sku": "CAN-PST-CAR", "unidade": "UN", "categoria": "CANTINA", "preco": 7.00, "local_id": 2, "family_name": "Salgados"},
        {"nome": "Coxinha de Frango", "sku": "CAN-COX-FRA", "unidade": "UN", "categoria": "CANTINA", "preco": 7.00, "local_id": 2, "family_name": "Salgados"},
        {"nome": "Pão de Queijo", "sku": "CAN-PDQ", "unidade": "UN", "categoria": "CANTINA", "preco": 4.50, "local_id": 2, "family_name": "Salgados"},
        {"nome": "Refrigerante Lata", "sku": "CAN-REF-LAT", "unidade": "UN", "categoria": "CANTINA", "preco": 5.00, "local_id": 2, "family_name": "Bebidas"},
        {"nome": "Água Mineral 500ml", "sku": "CAN-AGU-500", "unidade": "UN", "categoria": "CANTINA", "preco": 3.00, "local_id": 2, "family_name": "Bebidas"},
        {"nome": "Suco Lata", "sku": "CAN-SUC-LAT", "unidade": "UN", "categoria": "CANTINA", "preco": 6.00, "local_id": 2, "family_name": "Bebidas"},
        {"nome": "Chocolate Barra", "sku": "CAN-CHO-BAR", "unidade": "UN", "categoria": "CANTINA", "preco": 6.50, "local_id": 2, "family_name": "Doces & Chocolates"},
        {"nome": "Trident", "sku": "CAN-TRI-DEN", "unidade": "UN", "categoria": "CANTINA", "preco": 3.00, "local_id": 2, "family_name": "Doces & Chocolates"},
        # Fazendinha - Bebidas & Sucos
        {"nome": "Suco de Uva Integral 500ml", "sku": "FAZ-SUC-UVA", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 8.00, "local_id": 1, "family_name": "Bebidas & Sucos"},
        {"nome": "Suco de Laranja Natural 500ml", "sku": "FAZ-SUC-LAR", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 7.00, "local_id": 1, "family_name": "Bebidas & Sucos"},
        {"nome": "Refrigerante Coca-Cola Lata", "sku": "FAZ-REF-COK", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 5.00, "local_id": 1, "family_name": "Bebidas & Sucos"},
        {"nome": "Refrigerante Guaraná Lata", "sku": "FAZ-REF-GUA", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 5.00, "local_id": 1, "family_name": "Bebidas & Sucos"},
        # Fazendinha - Produtos Coloniais
        {"nome": "Queijo Minas Artesanal ICM", "sku": "FAZ-QJO-ICM", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 35.00, "local_id": 1, "family_name": "Produtos Coloniais"},
        {"nome": "Doce de Leite Colonial 500g", "sku": "FAZ-DDL-COL", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 20.00, "local_id": 1, "family_name": "Produtos Coloniais"},
        {"nome": "Mel Silvestre Maanaim 250g", "sku": "FAZ-MEL-MAA", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 15.00, "local_id": 1, "family_name": "Produtos Coloniais"},
        # Fazendinha - Lanches & Salgados
        {"nome": "Bolo Caseiro de Fubá", "sku": "FAZ-BOL-FUB", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 12.00, "local_id": 1, "family_name": "Lanches & Salgados"},
        {"nome": "Pão de Queijo Recheado", "sku": "FAZ-PDQ-REC", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 6.00, "local_id": 1, "family_name": "Lanches & Salgados"},
        # Fazendinha - Lembranças ICM
        {"nome": "Caneca Personalizada ICM", "sku": "FAZ-CAN-ICM", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 25.00, "local_id": 1, "family_name": "Lembranças ICM"},
        {"nome": "Chaveiro Madeira Maanaim", "sku": "FAZ-CHA-ICM", "unidade": "UN", "categoria": "FAZENDINHA", "preco": 8.00, "local_id": 1, "family_name": "Lembranças ICM"},
        # Livraria
        {"nome": "Bíblia de Estudo ACF", "sku": "LIV-BIB-ACF", "unidade": "UN", "categoria": "LIVRARIA", "preco": 120.00, "local_id": 4, "family_name": "Bíblias & Coletâneas"},
        {"nome": "Coletânea de Louvores ICM (Grande)", "sku": "LIV-COL-GRA", "unidade": "UN", "categoria": "LIVRARIA", "preco": 50.00, "local_id": 4, "family_name": "Bíblias & Coletâneas"},
        {"nome": "Coletânea de Louvores ICM (Pequena)", "sku": "LIV-COL-PEQ", "unidade": "UN", "categoria": "LIVRARIA", "preco": 35.00, "local_id": 4, "family_name": "Bíblias & Coletâneas"},
        {"nome": "Livro O Tabernáculo", "sku": "LIV-TAB-01", "unidade": "UN", "categoria": "LIVRARIA", "preco": 45.00, "local_id": 4, "family_name": "Livros & Literatura"},
        {"nome": "Livro As Eras da Igreja", "sku": "LIV-ERA-01", "unidade": "UN", "categoria": "LIVRARIA", "preco": 38.00, "local_id": 4, "family_name": "Livros & Literatura"},
        # Secretaria
        {"nome": "Estadia Adicional Chalé", "sku": "SEC-EST-ADD", "unidade": "UN", "categoria": "SECRETARIA", "preco": 80.00, "local_id": 3, "family_name": "Serviços & Taxas"},
    ]

    # 3. Mapeamento de produtos existentes a associar
    existing_associations = [
        # Livraria (4) -> Bíblias & Coletâneas
        {"sku": "COL-COM-01", "local_id": 4, "family_name": "Bíblias & Coletâneas", "preco": 40.00},
        {"sku": "COL-NV2-01", "local_id": 4, "family_name": "Bíblias & Coletâneas", "preco": 35.00},
        {"sku": "COL-LVA-01", "local_id": 4, "family_name": "Bíblias & Coletâneas", "preco": 30.00},
        {"sku": "COL-NV1-01", "local_id": 4, "family_name": "Bíblias & Coletâneas", "preco": 30.00},
        {"sku": "COL-CIA-01", "local_id": 4, "family_name": "Bíblias & Coletâneas", "preco": 25.00},
        # Secretaria (3) -> Inscrições
        {"sku": "INS-SEM-01", "local_id": 3, "family_name": "Inscrições", "preco": 180.00},
        {"sku": "INS-VOL-01", "local_id": 3, "family_name": "Inscrições", "preco": 90.00},
        {"sku": "INS-VOL-02", "local_id": 3, "family_name": "Inscrições", "preco": 180.00},
        # Secretaria (3) -> Serviços & Taxas
        {"sku": "CRACHA-01", "local_id": 3, "family_name": "Serviços & Taxas", "preco": 5.00},
    ]

    async with engine.begin() as conn:
        print("🌱 Criando Famílias de Produtos...")
        for fam in families_data:
            await conn.execute(
                text("""
                    INSERT INTO pos_familiavenda (nome, local_id)
                    VALUES (:nome, :local_id)
                    ON CONFLICT (local_id, nome) DO NOTHING
                """),
                fam
            )

        # Buscar IDs das famílias criadas/existentes
        res = await conn.execute(text("SELECT id, local_id, nome FROM pos_familiavenda"))
        families_map = {(r[1], r[2]): r[0] for r in res.fetchall()}

        print("📦 Criando Produtos Centrais e Associando aos PDVs...")
        for prod in new_products:
            # 1. Inserir produto central se não existir
            await conn.execute(
                text("""
                    INSERT INTO inventory_produto 
                        (nome, sku, unidade, estoque_atual, estoque_minimo, estoque_maximo, 
                         ativo, custo_medio_atual, valor_estoque_atual, categoria, estoque_reabastecimento, perene)
                    VALUES 
                        (:nome, :sku, :unidade, 100.0, 5.0, 500.0, 
                         true, :custo, :valor_est, :categoria, 10.0, true)
                    ON CONFLICT (sku) DO NOTHING
                """),
                {
                    "nome": prod["nome"],
                    "sku": prod["sku"],
                    "unidade": prod["unidade"],
                    "custo": prod["preco"] * 0.5, # 50% de custo fictício
                    "valor_est": (prod["preco"] * 0.5) * 100,
                    "categoria": prod["categoria"]
                }
            )

            # Buscar ID do produto central
            p_res = await conn.execute(
                text("SELECT id FROM inventory_produto WHERE sku = :sku"),
                {"sku": prod["sku"]}
            )
            prod_id = p_res.scalar_one()

            # Buscar ID da família correspondente
            fam_id = families_map.get((prod["local_id"], prod["family_name"]))

            # Associar localmente
            await conn.execute(
                text("""
                    INSERT INTO pos_produtolocal 
                        (preco_venda, estoque_atual, estoque_minimo, ponto_reabastecimento, estoque_maximo, 
                         ativo, criado_em, familia_id, local_id, produto_id)
                    VALUES 
                        (:preco, 50.0, 5.0, 10.0, 200.0, 
                         true, NOW(), :fam_id, :local_id, :prod_id)
                    ON CONFLICT (produto_id, local_id) DO NOTHING
                """),
                {
                    "preco": prod["preco"],
                    "fam_id": fam_id,
                    "local_id": prod["local_id"],
                    "prod_id": prod_id
                }
            )

        print("🔗 Associando Produtos Existentes aos PDVs...")
        for assoc in existing_associations:
            # Buscar ID do produto central
            p_res = await conn.execute(
                text("SELECT id FROM inventory_produto WHERE sku = :sku"),
                {"sku": assoc["sku"]}
            )
            row = p_res.fetchone()
            if not row:
                print(f"⚠️ Produto com SKU {assoc['sku']} não encontrado. Pulando.")
                continue
            prod_id = row[0]

            # Buscar ID da família correspondente
            fam_id = families_map.get((assoc["local_id"], assoc["family_name"]))

            # Associar localmente
            await conn.execute(
                text("""
                    INSERT INTO pos_produtolocal 
                        (preco_venda, estoque_atual, estoque_minimo, ponto_reabastecimento, estoque_maximo, 
                         ativo, criado_em, familia_id, local_id, produto_id)
                    VALUES 
                        (:preco, 20.0, 2.0, 5.0, 100.0, 
                         true, NOW(), :fam_id, :local_id, :prod_id)
                    ON CONFLICT (produto_id, local_id) DO NOTHING
                """),
                {
                    "preco": assoc["preco"],
                    "fam_id": fam_id,
                    "local_id": assoc["local_id"],
                    "prod_id": prod_id
                }
            )

    await engine.dispose()
    print("🎉 Seed de produtos e famílias concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed_data())
