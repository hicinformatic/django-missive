/**
 * Adapte l'affichage des champs du destinataire selon le contexte de la missive
 */
(function initRecipientContextFilter() {
    'use strict';

    // Attendre que django.jQuery soit disponible
    if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
        setTimeout(initRecipientContextFilter, 50);
        return;
    }

    var $ = django.jQuery;

    // Mapping des types de missives vers les champs requis
    var FIELDS_BY_MISSIVE_TYPE = {
        'EMAIL': {
            required: ['email'],
            optional: ['name', 'recipient_type', 'content_type', 'object_id', 'civility', 'notes', 'metadata', 'is_active'],
            hidden: ['mobile', 'address_line1', 'address_line2', 'address_line3', 'postal_code', 'city', 'state', 'country']
        },
        'SMS': {
            required: ['mobile'],
            optional: ['name', 'recipient_type', 'content_type', 'object_id', 'civility', 'notes', 'metadata', 'is_active'],
            hidden: ['email', 'address_line1', 'address_line2', 'address_line3', 'postal_code', 'city', 'state', 'country']
        },
        'WHATSAPP': {
            required: ['mobile'],
            optional: ['name', 'recipient_type', 'content_type', 'object_id', 'civility', 'notes', 'metadata', 'is_active'],
            hidden: ['email', 'address_line1', 'address_line2', 'address_line3', 'postal_code', 'city', 'state', 'country']
        },
        'POSTAL': {
            required: ['address_line1', 'postal_code', 'city', 'country'],
            optional: ['name', 'recipient_type', 'content_type', 'object_id', 'civility', 'address_line2', 'address_line3', 'state', 'notes', 'metadata', 'is_active'],
            hidden: ['email', 'mobile']
        },
        'NOTIFICATION': {
            required: ['email'],
            optional: ['name', 'recipient_type', 'content_type', 'object_id', 'civility', 'notes', 'metadata', 'is_active'],
            hidden: ['mobile', 'address_line1', 'address_line2', 'address_line3', 'postal_code', 'city', 'state', 'country']
        }
    };

    function getMissiveTypeFromURL() {
        // Détecter le type de missive depuis l'URL ou le referrer
        var url = window.location.href;
        var referrer = document.referrer;
        
        // Chercher dans les paramètres GET
        var params = new URLSearchParams(window.location.search);
        if (params.has('missive_type')) {
            return params.get('missive_type');
        }
        
        // Chercher dans le referrer (si on vient d'une page de missive)
        if (referrer && referrer.includes('/missive/missive/')) {
            if (referrer.includes('missive_type=')) {
                var match = referrer.match(/missive_type=([A-Z]+)/);
                if (match) {
                    return match[1];
                }
            }
        }
        
        return null;
    }

    function adaptFieldsVisibility(missiveType) {
        if (!missiveType || !FIELDS_BY_MISSIVE_TYPE[missiveType]) {
            return; // Afficher tous les champs par défaut
        }

        var config = FIELDS_BY_MISSIVE_TYPE[missiveType];
        var allFields = config.required.concat(config.optional).concat(config.hidden);

        // Masquer les champs non pertinents
        config.hidden.forEach(function(fieldName) {
            var $field = $('.field-' + fieldName);
            if ($field.length) {
                $field.hide();
            }
        });

        // Ajouter des indicateurs visuels pour les champs requis
        config.required.forEach(function(fieldName) {
            var $field = $('.field-' + fieldName);
            if ($field.length) {
                $field.show();
                var $label = $field.find('label');
                if ($label.length && !$label.find('.required-indicator').length) {
                    $label.append(' <span class="required-indicator" style="color: #dc3545;">*</span>');
                }
            }
        });

        // Afficher les champs optionnels
        config.optional.forEach(function(fieldName) {
            var $field = $('.field-' + fieldName);
            if ($field.length) {
                $field.show();
            }
        });

        // Ajouter un message d'information en haut du formulaire
        addContextMessage(missiveType);
    }

    function addContextMessage(missiveType) {
        var messages = {
            'EMAIL': '✉️ Mode Email : Seuls les champs liés à l\'email sont affichés',
            'SMS': '📱 Mode SMS : Seuls les champs liés au téléphone sont affichés',
            'WHATSAPP': '💬 Mode WhatsApp : Seuls les champs liés au téléphone sont affichés',
            'POSTAL': '📮 Mode Courrier : Seuls les champs liés à l\'adresse postale sont affichés',
            'NOTIFICATION': '🔔 Mode Notification : Seuls les champs liés à l\'email sont affichés'
        };

        var message = messages[missiveType];
        if (!message) {
            return;
        }

        // Vérifier si le message n'existe pas déjà
        if ($('#recipient-context-message').length) {
            return;
        }

        var $message = $('<div id="recipient-context-message" style="' +
            'background-color: #d1ecf1; ' +
            'border: 1px solid #bee5eb; ' +
            'color: #0c5460; ' +
            'padding: 12px 20px; ' +
            'margin: 20px 0; ' +
            'border-radius: 4px; ' +
            'font-size: 14px;' +
            '">' + message + '</div>');

        // Insérer le message après le titre du formulaire
        $('h1').first().after($message);
    }

    // Initialiser au chargement de la page
    $(document).ready(function() {
        setTimeout(function() {
            var missiveType = getMissiveTypeFromURL();
            if (missiveType) {
                adaptFieldsVisibility(missiveType);
            }
        }, 100);
    });

})();

