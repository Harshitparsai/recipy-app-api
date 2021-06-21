from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipy.serializers import IngredientSerializer

INGREDIENT_URLS = reverse('recipy:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test publically available ingredient api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test private ingredient api"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@inviz.ai',
            'test123'
        )
        self.client.force_authenticate(self.user)

    def test_retreive_ingredient_list(self):
        """Test retreiving a list of ingredients"""
        Ingredient.objects.create(
            user=self.user,
            name='Kale'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Salt'
        )
        res = self.client.get(INGREDIENT_URLS)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_authenticate_user(self):
        """Test the ingredients of only authenticated users are returned"""
        user2 = get_user_model().objects.create_user(
            'other@inviz.ai',
            'other123'
        )
        Ingredient.objects.create(
            user=user2,
            name='Venica'
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Tumeric'
        )
        res = self.client.get(INGREDIENT_URLS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test create a new ingredient"""
        payload = {'name': 'cabbage'}
        self.client.post(INGREDIENT_URLS, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENT_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
