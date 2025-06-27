import json

from rest_framework import serializers
from fhir.resources.patient import Patient
from .models import PatientResource
import uuid


class FHIRPatientSerializer(serializers.ModelSerializer):
    """
    Serializer for the PatientResource model.

    This serializer handles the conversion of FHIR Patient JSON data to and from
    the internal PatientResource model representation. It leverages the `fhir.resources`
    package for robust FHIR R4 validation of incoming data.
    """
    class Meta:
        model = PatientResource
        fields = ['resource_data']

    def to_internal_value(self, data):
        """
        Converts incoming request data into a validated internal representation
        suitable for saving to the PatientResource model. This is where FHIR
        validation happens.
        """

        # Ensure the incoming data is a dictionary
        if not isinstance(data, dict):
            raise serializers.ValidationError({'detail': "Invalid data format. Expected a JSON object"})

        # Ensure 'resourceType' is 'Patient' as expected for this endpoint
        if data.get('resourceType') != 'Patient':
            raise serializers.ValidationError({'resourceType': 'resourceType must be Patient'})

        try:
            # Parse and validate the incoming data against the FHIR Patient schema.
            # This uses fhir.resources to ensure FHIR compliance.
            fhir_patient = Patient.parse_obj(data)
        except Exception as e:
            # If validation fails, raise a DRF ValidationError
            raise serializers.ValidationError(f"Invalid FHIR Patient resource: {e}")

        resource_data_dict = json.loads(fhir_patient.json(exclude_unset=True))

        # The internal representation for our PatientResource model
        # We store the validated FHIR JSON directly in the 'data' field.
        # The 'fhir_id' will be extracted from fhir_patient.id or generated.
        internal_data = {
            'resource_data': resource_data_dict  # Convert back to dict, exclude unset fields
        }

        # If an 'id' is provided in the FHIR resource, use it as our fhir_id.
        # This is important for client assigned IDs or updates
        if fhir_patient.id:
            internal_data['fhir_id'] = fhir_patient.id
        else:
            # If no ID is provided in the FHIR resource, we will generate one during creation.
            # For updates, an ID must be present in the URL path.
            pass

        return internal_data

    def to_representation(self, instance):
        """
        Converts the PatientResource model instance into the outgoing API representation

        (A complete FHIR Patient resource JSON).
        """
        return instance.resource_data

    def create(self, validated_data):
        """
        Handles the creation of a new PatientData instance
        Ensures FHIR ID uniqueness and generates one if not provided by the client
        """

        fhir_id_from_data = validated_data.get('fhir_id')
        fhir_json_data = validated_data['resource_data']

        if fhir_id_from_data:
            # If an ID was provided in the incoming FHIR data, check for uniqueness
            if PatientResource.objects.filter(fhir_id=fhir_id_from_data).exists():
                raise serializers.ValidationError({'id': f"A patient with FHIR ID '{fhir_id_from_data}' already exists."})

            else:
                # If no FHIR ID was provided in the incoming data, generate a UUID.
                # This UUID will serve as both the model's fhir_id and the FHIR resource's id.
                generated_fhir_id = str(uuid.uuid4())
                validated_data['fhir_id'] = generated_fhir_id

                # Also update the 'id' field within the FHIR JSON data itself to match the generated ID
                fhir_json_data['id'] = generated_fhir_id

        # Create the PatientResource instance in the database.
        patient_instance = PatientResource.objects.create(**validated_data)
        return patient_instance
    def update(self, instance, validated_data):
        """
        Handles the update of an existing PatientResource instance
        """
        # For updates, we primarily update the 'resource_data' JSON field
        # The fhir_id should not change during an update operation
        # as it's part of the resource's identity.

        resource_data_for_db = validated_data['resource_data']
        if not isinstance(resource_data_for_db, dict):
            if hasattr(resource_data_for_db, 'dict'):
                resource_data_for_db = resource_data_for_db.dict(exclude_unset=True)
            else:
                raise TypeError(
                    f"resource_data is of unexpected type {type(resource_data_for_db).__name__} and cannot be serialized.")

        instance.resource_data = resource_data_for_db
        instance.save()
        return instance

