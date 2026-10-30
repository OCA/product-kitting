# Copyright 2026 Tecnativa - Adasat Torres
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestKitTotalWeightVolume(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ProductCategory = cls.env["product.category"]
        ProductProduct = cls.env["product.product"]
        MRPBom = cls.env["mrp.bom"]
        cls.product_category = ProductCategory.create(
            {
                "name": "Test category",
            }
        )
        cls.product1 = ProductProduct.create(
            {
                "name": "Test 1",
                "list_price": 100,
                "type": "consu",
                "categ_id": cls.product_category.id,
            }
        )
        cls.product2 = ProductProduct.create(
            {
                "name": "Test 2",
                "list_price": 100,
                "type": "consu",
                "categ_id": cls.product_category.id,
                "volume": 10,
                "weight": 10,
            }
        )
        cls.product3 = ProductProduct.create(
            {
                "name": "Test 2",
                "list_price": 100,
                "type": "consu",
                "categ_id": cls.product_category.id,
                "volume": 10,
                "weight": 10,
            }
        )
        cls.bom_id = MRPBom.create(
            {
                "product_tmpl_id": cls.product1.product_tmpl_id.id,
                "product_id": cls.product1.id,
                "type": "phantom",
                "bom_line_ids": [
                    Command.create({"product_id": cls.product2.id, "product_qty": 1.0}),
                    Command.create({"product_id": cls.product3.id, "product_qty": 2.0}),
                ],
            }
        )

    def test_kit_weight_volume_change_uom(self):
        unit = self.product1.uom_id
        dozen = self.env.ref("uom.product_uom_dozen")
        self.assertEqual(self.product1.volume, 30)
        self.assertEqual(self.product1.weight, 30)

        self.product1.write({"uom_id": dozen.id, "uom_po_id": dozen.id})
        self.assertEqual(self.bom_id.product_uom_id, unit)
        self.assertEqual(self.product1.volume, 360)
        self.assertEqual(self.product1.weight, 360)

        self.product1.write({"uom_id": unit.id, "uom_po_id": unit.id})
        self.assertEqual(self.product1.volume, 30)
        self.assertEqual(self.product1.weight, 30)

    def test_product_weight_volume(self):
        self.assertEqual(self.product1.volume, 30)
        self.assertEqual(self.product1.weight, 30)
        self.product2.volume = 30
        self.product3.volume = 100
        self.assertEqual(self.product1.volume, 230)
        self.product2.weight = 15
        self.product3.weight = 50
        self.assertEqual(self.product1.weight, 115)
        self.product4 = self.env["product.product"].create(
            {
                "name": "Test 4",
                "type": "consu",
                "categ_id": self.product_category.id,
                "volume": 10,
                "weight": 10,
            }
        )
        self.bom_id.write(
            {
                "bom_line_ids": [
                    Command.create(
                        {"product_id": self.product4.id, "product_qty": 2.0}
                    ),
                ]
            }
        )
        self.assertEqual(self.product1.weight, 135)
        self.assertEqual(self.product1.volume, 250)
        self.product5 = self.env["product.product"].create(
            {
                "name": "Test 5",
                "type": "consu",
                "categ_id": self.product_category.id,
                "volume": 5,
                "weight": 5,
            }
        )
        self.bom_id.bom_line_ids.filtered(
            lambda line: line.product_id == self.product4
        ).write({"product_id": self.product5.id})
        self.assertEqual(self.product1.volume, 240)
        self.assertEqual(self.product1.weight, 125)
        self.bom_id.product_qty = 2
        self.assertEqual(self.product1.volume, 120)
        self.assertEqual(self.product1.weight, 62.5)
        self.product6 = self.env["product.product"].create(
            {
                "name": "Test 6",
                "type": "consu",
                "categ_id": self.product_category.id,
                "volume": 1,
                "weight": 1,
            }
        )
        self.bom_id.write(
            {
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product6.id,
                            "product_qty": 1.0,
                            "product_uom_id": self.env.ref("uom.product_uom_dozen").id,
                        }
                    )
                ]
            }
        )
        self.assertEqual(self.product1.volume, 126)
        self.assertEqual(self.product1.weight, 68.5)

    def test_post_init_hook(self):
        # Existing kits keep a stale stored value until the hook recomputes them
        self.product1.write({"volume": 999, "weight": 999})
        self.assertEqual(self.product1.volume, 999)
        self.assertEqual(self.product1.weight, 999)
        post_init_hook(self.env)
        self.assertEqual(self.product1.volume, 30)
        self.assertEqual(self.product1.weight, 30)
