/**
 * Filtre dynamique des providers selon le type de missive sélectionné
 */
(function initProviderFilter() {
    'use strict';

    // Attendre que django.jQuery soit disponible
    if (typeof django === 'undefined' || typeof django.jQuery === 'undefined') {
        setTimeout(initProviderFilter, 50);
        return;
    }

    var $ = django.jQuery;

    // Mapping des types de missives vers leurs providers compatibles
    // Sera chargé depuis l'attribut data-providers-config du widget
    let PROVIDERS_BY_TYPE = {};
    
    // Tous les providers disponibles (pour restaurer la liste complète)
    let allProviders = [];
    
    // Charger la configuration depuis l'attribut data du widget
    function loadProvidersConfig() {
        const $providerChoice = $('#id_provider_choice');
        if ($providerChoice.length) {
            const configData = $providerChoice.attr('data-providers-config');
            if (configData) {
                try {
                    PROVIDERS_BY_TYPE = JSON.parse(configData);
                } catch (e) {
                    // Fallback sur une config par défaut
                    PROVIDERS_BY_TYPE = {
                        'EMAIL': ['django_email', 'sendgrid', 'mailgun', 'custom'],
                        'SMS': ['twilio', 'custom'],
                        'BRANDED': ['twilio', 'slack', 'telegram', 'custom'],
                        'POSTAL': ['laposte', 'custom'],
                        'POSTAL_REGISTERED': ['laposte', 'maileva', 'custom'],
                        'NOTIFICATION': ['custom']
                    };
                }
            }
        }
    }

    function filterProviders() {
        const $missiveType = $('#id_missive_type');
        const $providerChoice = $('#id_provider_choice');
        
        if (!$missiveType.length || !$providerChoice.length) {
            // Réessayer après un court délai si les éléments ne sont pas encore présents
            setTimeout(filterProviders, 100);
            return;
        }

        // Sauvegarder tous les providers au premier chargement
        if (allProviders.length === 0) {
            $providerChoice.find('option').each(function() {
                allProviders.push({
                    value: $(this).val(),
                    text: $(this).text()
                });
            });
        }

        const selectedType = $missiveType.val();
        const currentProvider = $providerChoice.val();
        
        if (selectedType && PROVIDERS_BY_TYPE[selectedType]) {
            const compatibleProviders = PROVIDERS_BY_TYPE[selectedType];
            
            // Vider la liste actuelle
            $providerChoice.empty();
            
            // Ajouter uniquement les providers compatibles
            allProviders.forEach(function(provider) {
                if (compatibleProviders.includes(provider.value)) {
                    $providerChoice.append(
                        $('<option></option>')
                            .val(provider.value)
                            .text(provider.text)
                    );
                }
            });
            
            // Restaurer la sélection si elle est toujours compatible
            if (compatibleProviders.includes(currentProvider)) {
                $providerChoice.val(currentProvider);
            } else {
                // Sinon, sélectionner le premier provider compatible
                if (compatibleProviders.length > 0) {
                    // Pour EMAIL, préférer django_email
                    if (selectedType === 'EMAIL' && compatibleProviders.includes('django_email')) {
                        $providerChoice.val('django_email');
                    } else if (selectedType === 'SMS' && compatibleProviders.includes('twilio')) {
                        $providerChoice.val('twilio');
                    } else if (selectedType === 'BRANDED' && compatibleProviders.includes('twilio')) {
                        $providerChoice.val('twilio');
                    } else if (selectedType === 'POSTAL' && compatibleProviders.includes('laposte')) {
                        $providerChoice.val('laposte');
                    } else if (selectedType === 'POSTAL_REGISTERED' && compatibleProviders.includes('laposte')) {
                        $providerChoice.val('laposte');
                    } else {
                        $providerChoice.val(compatibleProviders[0]);
                    }
                }
            }
        } else {
            // Si aucun type n'est sélectionné, restaurer tous les providers
            $providerChoice.empty();
            allProviders.forEach(function(provider) {
                $providerChoice.append(
                    $('<option></option>')
                        .val(provider.value)
                        .text(provider.text)
                );
            });
            $providerChoice.val(currentProvider);
        }
    }

    // Initialiser au chargement de la page
    $(document).ready(function() {
        // Charger la configuration des providers depuis l'attribut data
        loadProvidersConfig();
        
        // Filtrer immédiatement si un type est déjà sélectionné
        setTimeout(function() {
            filterProviders();
            
            // Écouter les changements sur le champ type de missive
            $('#id_missive_type').on('change', function() {
                filterProviders();
            });
        }, 100);
    });

})();
