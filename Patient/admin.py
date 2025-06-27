from django.contrib import admin
from .models import PatientResource


@admin.register(PatientResource)
class PatientDataAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PatientData model.
    """
    # Fields to display in the list view of the admin interface
    list_display = ('fhir_id', 'get_patient_name', 'gender_display', 'birth_date_display', 'created_at', 'updated_at')
    # Fields to make clickable links to the detail view
    list_display_links = ('fhir_id', )
    # Fields to allow searching by
    search_fields = ('fhir_id', 'data__name__given__0', 'data__name__family', 'data__gender')
    # Fields to filter the list by
    list_filter = ('created_at', 'updated_at')
    # Fields to make read-only in the admin detail view
    readonly_fields = ('created_at', 'updated_at')

    # Custom methods to display data from the JSONField in a more readable format
    def get_patient_name(self, obj):
        """
        Extracts and returns the patient's official name from the FHIR JSON data.
        """
        if obj.resource_data and 'name' in obj.resource_data and obj.resource_data['name']:
            for name_obj in obj.resource_data['name']:
                if name_obj.get('use') == 'official':
                    given = " ".join(name_obj.get('given', []))
                    family = name_obj.get('family', '')
                    return f"{given} {family}".strip()
            # If no official name, try to get any name
            name_obj = obj.resource_data['name'][0]
            given = " ".join(name_obj.get('given', []))
            family = name_obj.get('family', '')
            return f"{given} {family}".strip()
        return "N/A"
    get_patient_name.short_description = 'Patient Name' # Column header in admin list

    def gender_display(self, obj):
        """
        Extracts and returns the patient's gender from the FHIR JSON data.
        """
        return obj.resource_data.get('gender', 'N/A')
    gender_display.short_description = 'Gender'

    def birth_date_display(self, obj):
        """
        Extracts and returns the patient's birth date from the FHIR JSON data.
        """
        return obj.resource_data.get('birthDate', 'N/A')
    birth_date_display.short_description = 'Birth Date'

    # Fieldsets for organizing fields in the admin detail view
    fieldsets = (
        (None, {
            'fields': ('fhir_id', 'resource_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',), # Makes this section collapsible
        }),
    )

