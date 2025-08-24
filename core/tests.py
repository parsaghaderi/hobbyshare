from django.utils import timezone
from django.db import connection
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Hobby, Category, Tag, Application, Requirement, Rating, ParticipantRating
import threading, time


class APIFullFlowTests(APITestCase):
	def setUp(self):
		self.host = User.objects.create_user(username='host', password='pass')
		self.user1 = User.objects.create_user(username='u1', password='pass')
		self.user2 = User.objects.create_user(username='u2', password='pass')
		self.category = Category.objects.create(name='Outdoors')
		self.tag = Tag.objects.create(name='Camping')

	def auth(self, user):
		self.client = APIClient()
		self.client.login(username=user.username, password='pass')
		return self.client

	def create_hobby(self):
		c = self.auth(self.host)
		url = '/api/hobbies/'
		data = {
			'title': 'Weekend Hike',
			'description': 'Enjoy nature',
			'category_id': self.category.id,
			'tag_ids': [self.tag.id],
			'max_participants': 3,
			'date': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
			'place': 'Trailhead',
			'province': 'Ontario',
			'city': 'Toronto',
			'neighbourhood': 'Downtown'
		}
		resp = c.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
		return resp.data['id']

	def test_full_participation_and_rating_flow(self):
		hobby_id = self.create_hobby()
		# user1 & user2 apply
		for u in [self.user1, self.user2]:
			c = self.auth(u)
			resp = c.post(f'/api/hobbies/{hobby_id}/apply/')
			self.assertIn(resp.status_code, (200,201))
		# host accepts user1 only
		host_client = self.auth(self.host)
		apps = host_client.get('/api/applications/').json()['results'] if 'results' in host_client.get('/api/applications/').json() else host_client.get('/api/applications/').json()
		target_app = next(a for a in apps if a['applicant']['username']=='u1')
		resp = host_client.post(f"/api/applications/{target_app['id']}/set_status/", {'status':'accepted'})
		self.assertEqual(resp.status_code, 200)
		# Add approved requirement by host
		req_resp = host_client.post('/api/requirements/', {'hobby': hobby_id, 'name':'Tent'})
		self.assertEqual(req_resp.status_code, 201)
		req_id = req_resp.data['id']
		# Accepted user claims requirement
		u1_client = self.auth(self.user1)
		claim_resp = u1_client.post(f'/api/requirements/{req_id}/claim/')
		self.assertEqual(claim_resp.status_code, 200)
		# Fast-forward date to past: directly modify model
		h = Hobby.objects.get(id=hobby_id)
		h.date = timezone.now() - timezone.timedelta(hours=1)
		h.save()
		# user1 rates host
		rate_resp = u1_client.post(f'/api/hobbies/{hobby_id}/rate_host/', {'score':5,'comment':'Great','anonymous':False})
		self.assertEqual(rate_resp.status_code, 200)
		self.assertEqual(Rating.objects.filter(hobby_id=hobby_id).count(),1)
		# Host rates participant user1
		pr_resp = host_client.post('/api/participant-ratings/', {'hobby':hobby_id,'participant':self.user1.id,'score':4,'comment':'Good participant'})
		self.assertEqual(pr_resp.status_code,201)
		# Filtering
		list_resp = self.client.get('/api/hobbies/?province=Ontario&city=Toronto')
		self.assertEqual(list_resp.status_code,200)
		self.assertTrue(any(item['id']==hobby_id for item in (list_resp.json().get('results') or [])))

	def test_requirement_suggestion_approval(self):
		hobby_id = self.create_hobby()
		# apply & accept user1
		self.auth(self.user1).post(f'/api/hobbies/{hobby_id}/apply/')
		host_client = self.auth(self.host)
		app = Application.objects.get(applicant=self.user1, hobby_id=hobby_id)
		host_client.post(f'/api/applications/{app.id}/set_status/', {'status':'accepted'})
		# user1 suggests requirement
		u1_client = self.auth(self.user1)
		sugg_resp = u1_client.post('/api/requirements/', {'hobby':hobby_id,'name':'Snacks'})
		self.assertEqual(sugg_resp.status_code,201)
		req_id = sugg_resp.data['id']
		self.assertFalse(sugg_resp.data['is_approved'])
		# host approves
		approve_resp = host_client.post(f'/api/requirements/{req_id}/approve/')
		self.assertEqual(approve_resp.status_code,200)
		self.assertTrue(approve_resp.data['is_approved'])

	def test_capacity_limit(self):
		hobby_id = self.create_hobby()
		applicants = [self.user1, self.user2]
		for u in applicants:
			self.auth(u).post(f'/api/hobbies/{hobby_id}/apply/')
		host_client = self.auth(self.host)
		# accept both, capacity 3 so both accepted fine
		for app in Application.objects.filter(hobby_id=hobby_id):
			host_client.post(f'/api/applications/{app.id}/set_status/', {'status':'accepted'})
		# add extra user exceeding capacity
		user3 = User.objects.create_user(username='u3', password='pass')
		self.auth(user3).post(f'/api/hobbies/{hobby_id}/apply/')
		app3 = Application.objects.get(applicant__username='u3', hobby_id=hobby_id)
		# capacity still allows (3rd) -> adjust hobby capacity to 2 to force full
		h = Hobby.objects.get(id=hobby_id)
		h.max_participants = 2
		h.save()
		resp = host_client.post(f'/api/applications/{app3.id}/set_status/', {'status':'accepted'})
		self.assertEqual(resp.status_code,400)

class APIStressTests(APITestCase):
	def setUp(self):
		self.host = User.objects.create_user(username='host', password='pass')
		self.category = Category.objects.create(name='StressCat')

	def test_concurrent_applications(self):
		client = APIClient(); client.login(username='host', password='pass')
		resp = client.post('/api/hobbies/', {
			'title':'Stress','description':'x','category_id':self.category.id,
			'max_participants':1,
			'date':(timezone.now()+timezone.timedelta(days=1)).isoformat(),
			'place':'P','province':'Ontario','city':'Toronto','neighbourhood':'Downtown'
		}, format='json')
		self.assertEqual(resp.status_code,201)
		hobby_id = resp.data['id']

		users = [User.objects.create_user(username=f'su{i}', password='p') for i in range(10)]

		if connection.vendor == 'sqlite':
			# SQLite can't handle our previous threaded auth writes reliably. Simulate rapid sequential applications.
			for u in users:
				c = APIClient(); c.login(username=u.username, password='p')
				r = c.post(f'/api/hobbies/{hobby_id}/apply/')
				self.assertIn(r.status_code, (200,201))
		else:
			# Keep a lightweight concurrency scenario for non-sqlite engines.
			results = []
			def apply(u):
				c = APIClient(); c.login(username=u.username, password='p')
				results.append(c.post(f'/api/hobbies/{hobby_id}/apply/').status_code)
			threads = [threading.Thread(target=apply, args=(u,)) for u in users]
			for t in threads: t.start()
			for t in threads: t.join()

		self.assertEqual(Application.objects.filter(hobby_id=hobby_id).count(), 10)
		host_client = APIClient(); host_client.login(username='host', password='pass')
		first_id = Application.objects.filter(hobby_id=hobby_id).first().id
		accept_resp = host_client.post(f'/api/applications/{first_id}/set_status/', {'status':'accepted'})
		self.assertEqual(accept_resp.status_code,200)
		# Attempt to accept a second
		for app in Application.objects.filter(hobby_id=hobby_id).exclude(id=first_id)[:3]:
			second = host_client.post(f'/api/applications/{app.id}/set_status/', {'status':'accepted'})
			if second.status_code == 200:
				self.fail('Capacity breach: more than one accepted application')
		self.assertEqual(Application.objects.filter(hobby_id=hobby_id, status='accepted').count(),1)
