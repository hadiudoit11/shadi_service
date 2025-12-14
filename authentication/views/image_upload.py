from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os


class ImageUploadAPIView(APIView):
    """Image upload endpoint for vendor portfolio images"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        operation_id='upload_image',
        summary="Upload image",
        description="Upload an image file and get the URL back",
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Image file to upload'
                    },
                    'folder': {
                        'type': 'string',
                        'description': 'Optional folder name (e.g., "portfolio", "vendor-logos")'
                    }
                },
                'required': ['image']
            }
        },
        responses={
            200: OpenApiResponse(description="Image uploaded successfully"),
            400: OpenApiResponse(description="Invalid file or upload error"),
        },
        tags=['Images']
    )
    def post(self, request):
        """Upload image file"""
        if 'image' not in request.FILES:
            return Response(
                {'success': False, 'message': 'No image file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        folder = request.data.get('folder', 'uploads')
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response(
                {'success': False, 'message': 'Invalid file type. Only JPEG, PNG, and WebP allowed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return Response(
                {'success': False, 'message': 'File too large. Maximum size is 5MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate unique filename
            file_extension = os.path.splitext(image_file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"{folder}/{unique_filename}"
            
            # Save file to storage (local or S3)
            file_name = default_storage.save(file_path, ContentFile(image_file.read()))
            file_url = default_storage.url(file_name)
            
            return Response({
                'success': True,
                'message': 'Image uploaded successfully',
                'data': {
                    'filename': unique_filename,
                    'url': file_url,
                    'path': file_name,
                    'size': image_file.size,
                    'content_type': image_file.content_type
                }
            })
            
        except Exception as e:
            return Response(
                {'success': False, 'message': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )