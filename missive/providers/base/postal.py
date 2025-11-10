"""
Mixin pour les fonctionnalités courrier postal des providers.
"""
from typing import Any, Dict, List, Optional


class BasePostalMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques au courrier postal.
    """

    def get_postal_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du compte/service Courrier postal.
        
        Retourne les informations importantes pour le service postal :
        - Crédits disponibles (montant en euros généralement)
        - Limites et tarifs
        - État du service (actif/inactif)
        - Options disponibles (recommandé, suivi, signature, etc.)
        
        Returns:
            Dict contenant :
                - credits: Montant disponible (généralement en euros)
                - credits_type: 'amount' (montant en €)
                - is_available: bool, service accessible
                - limits: Dict avec les limites
                - warnings: Liste des alertes
                - options: Liste des options disponibles (recommandé, suivi, etc.)
                - details: Dict avec infos supplémentaires
        
        À surcharger dans les providers concrets.
        """
        return {
            "credits": None,
            "credits_type": "amount",
            "is_available": None,
            "limits": {},
            "warnings": ["Méthode get_postal_service_info() non implémentée pour ce provider"],
            "options": [],
            "details": {},
        }

    def send_postal(self) -> bool:
        """
        Envoie un courrier postal. À surcharger dans les providers concrets.

        Returns:
            bool: True si succès, False sinon
        """
        from ...models import MissiveStatus

        # Vérifier qu'on a une adresse
        if not self.missive.get_recipient_address():
            self._update_status(
                MissiveStatus.FAILED, error_message="Pas d'adresse postale"
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_postal()"
        )

    def validate_postal_address(self, address: str) -> Dict[str, Any]:
        """
        Valide une adresse postale.

        Vérifie :
        - Présence des éléments essentiels (rue, code postal, ville)
        - Format du code postal
        - Cohérence pays/code postal

        Args:
            address: Adresse postale complète (multi-lignes)

        Returns:
            Dict contenant :
            - is_valid (bool): Adresse valide
            - is_complete (bool): Tous les éléments présents
            - warnings (List[str]): Avertissements
            - parsed (Dict): Éléments détectés

        Example:
            result = provider.validate_postal_address(address)
            if not result['is_complete']:
                print("Adresse incomplète!")
        """
        warnings = []
        parsed = {}

        lines = [line.strip() for line in address.split("\n") if line.strip()]

        if len(lines) < 3:
            warnings.append("Adresse trop courte (minimum 3 lignes attendues)")

        # TODO: Parser l'adresse
        # - Détecter le code postal (regex par pays)
        # - Détecter la ville
        # - Vérifier cohérence code postal / ville (base de données)

        is_complete = len(lines) >= 3 and len(warnings) == 0

        return {
            "is_valid": len(lines) > 0,
            "is_complete": is_complete,
            "warnings": warnings,
            "parsed": parsed,
        }

    def calculate_postal_cost(
        self, weight_grams: int = 20, is_registered: bool = False, international: bool = False
    ) -> Dict[str, Any]:
        """
        Calcule le coût d'envoi d'un courrier postal.

        Args:
            weight_grams: Poids en grammes
            is_registered: Courrier recommandé
            international: Envoi international

        Returns:
            Dict contenant :
            - cost (float): Coût en euros
            - format (str): Format de courrier (lettre verte, prioritaire, etc.)
            - delivery_days (int): Délai de livraison estimé

        Example:
            cost_info = provider.calculate_postal_cost(weight_grams=50, is_registered=True)
            print(f"Coût: {cost_info['cost']}€")
        """
        # Grille tarifaire de base (La Poste France 2025)
        if international:
            base_cost = 1.96  # Lettre internationale
            delivery_days = 7
        else:
            if weight_grams <= 20:
                base_cost = 1.29  # Lettre verte
                delivery_days = 2
            elif weight_grams <= 100:
                base_cost = 1.96  # Lettre prioritaire
                delivery_days = 1
            else:
                base_cost = 3.15  # Grande enveloppe
                delivery_days = 2

        # Supplément recommandé
        if is_registered:
            base_cost += 4.50  # R1 (recommandé sans AR)
            # TODO: Différencier R1, R2, R3 selon le niveau de suivi

        return {
            "cost": base_cost,
            "format": "recommandé" if is_registered else "standard",
            "delivery_days": delivery_days,
            "weight_grams": weight_grams,
        }

    def prepare_postal_attachments(self, attachments: List) -> List[Dict[str, Any]]:
        """
        Prépare les pièces jointes pour impression/envoi postal.

        Les pièces jointes doivent être converties en PDF si nécessaire.

        Args:
            attachments: Liste de MissiveAttachment (triés par order)

        Returns:
            List[Dict]: Liste des fichiers prêts pour impression

        Example:
            files = provider.prepare_postal_attachments(missive.attachments.all())
            # → [{'filename': 'doc1.pdf', 'pages': 3}, ...]
        """
        prepared = []

        for attachment in attachments:
            file_info = {
                "filename": attachment.filename,
                "order": attachment.order,
                "mime_type": attachment.mime_type,
                "url": attachment.file_url,
            }

            # TODO: Convertir en PDF si nécessaire
            # if attachment.mime_type != 'application/pdf':
            #     # Convertir Word, Excel, images, etc. en PDF
            #     pdf_content = convert_to_pdf(attachment.file)
            #     file_info['converted'] = True

            prepared.append(file_info)

        return prepared

