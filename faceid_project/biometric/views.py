import numpy as np
from deepface import DeepFace
import base64
import io
import json
import os
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import FaceEncodingForm
from .models import FaceEncoding, DiaryEntry

# Загружаем модель Facenet
# FACENET_MODEL = DeepFace.build_model('Facenet')

def home(request):
    if not request.session.get('face_verified', False):
        return redirect('login')
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            request.session['face_verified'] = False  # Требуем фиксацию Face ID
            print(f"User {user.username} registered, redirecting to face_verify")
            return JsonResponse({'success': True, 'message': 'Пользователь зарегистрирован! Настройте Face ID.', 'redirect': '/face_verify/'})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Ошибка в форме.', 'errors': errors})
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Проверяем, зарегистрирован ли Face ID
            face_encoding_exists = FaceEncoding.objects.filter(user=user).exists()
            print(f"Checking FaceEncoding for user {user.username}: exists={face_encoding_exists}")
            if face_encoding_exists:
                request.session['face_verified'] = False  # Требуем проверку Face ID
                print(f"Redirecting to face_login for user {user.username}")
                return redirect('face_login')  # Перенаправляем на проверку Face ID
            else:
                print(f"Redirecting to face_verify for user {user.username}")
                return redirect('face_verify')  # Перенаправляем на регистрацию Face ID
        else:
            messages.error(request, 'Ошибка входа. Проверьте логин или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Вы вышли из системы.')
    return redirect('home')

@login_required
def upload_face(request):
    return redirect('face_verify')

@login_required
@csrf_exempt
def face_verify(request):
    print(f"face_verify called for user {request.user.username}")
    if request.method == 'POST':
        try:
            # Проверяем, есть ли уже Face ID у пользователя
            if FaceEncoding.objects.filter(user=request.user).exists():
                print(f"FaceEncoding already exists for {request.user.username}, redirecting to face_login")
                return JsonResponse({'success': False, 'message': 'Face ID уже зарегистрирован. Используйте проверку Face ID.', 'redirect': '/face_login/'})

            data = json.loads(request.body)
            image_data = data.get('image', '')
            if not image_data:
                print("No image data received")
                return JsonResponse({'success': False, 'message': 'Изображение не получено.'})

            # Декодируем base64 изображение
            try:
                image_data = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data)
            except base64.binascii.Error as e:
                print(f"Base64 decode error: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Ошибка декодирования base64: {str(e)}'})

            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.verify()
                image = Image.open(io.BytesIO(image_bytes))
                image_np = np.array(image.convert('RGB'))
            except Exception as e:
                print(f"Image validation error: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Невалидное изображение: {str(e)}'})

            # Извлекаем вектор лица
            try:
                captured_embedding = DeepFace.represent(
                    img_path=image_np,
                    model_name='Facenet',
                    enforce_detection=True,
                    detector_backend='ssd'
                )
                if not captured_embedding or not captured_embedding[0].get('embedding'):
                    print("DeepFace: No embedding found")
                    return JsonResponse({'success': False, 'message': 'Лицо не обнаружено. Убедитесь в хорошем освещении и правильном положении лица.'})
                captured_embedding = np.array(captured_embedding[0]['embedding'])
                print(f"Embedding extracted: {captured_embedding[:10]}...")
            except Exception as e:
                print(f"DeepFace error: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Ошибка DeepFace: {str(e)}'})

            # Сохраняем изображение в face_images
            image_path = f"face_images/{request.user.username}_face.jpg"
            full_path = os.path.join('media', image_path)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                image.save(full_path)
                print(f"Image saved at: {full_path}")
            except Exception as e:
                print(f"Error saving image: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Ошибка сохранения изображения: {str(e)}'})

            # Создаём и сохраняем FaceEncoding
            face_encoding = FaceEncoding(user=request.user)
            face_encoding.image = image_path
            face_encoding.set_encoding(captured_embedding)
            face_encoding.save()
            print(f"FaceEncoding saved for user: {request.user.username}, image: {face_encoding.image}")

            # Проверяем сохранённость
            saved_encoding = FaceEncoding.objects.get(user=request.user)
            if saved_encoding and saved_encoding.get_encoding() is not None and saved_encoding.image:
                print(f"FaceEncoding verified: image={saved_encoding.image}, encoding length={len(saved_encoding.get_encoding())}")
            else:
                print("FaceEncoding verification failed")
                return JsonResponse({'success': False, 'message': 'Ошибка: FaceEncoding не сохранён корректно.'})

            request.session['face_verified'] = True
            print(f"Session face_verified set to True for user {request.user.username}")
            messages.success(request, 'Face ID успешно зарегистрирован!')
            return JsonResponse({'success': True, 'message': 'Face ID успешно зарегистрирован!', 'redirect': '/home/'})

        except Exception as e:
            print(f"General error: {str(e)}")
            logout(request)
            messages.error(request, f'Ошибка обработки: {str(e)}')
            return JsonResponse({'success': False, 'message': f'Ошибка обработки: {str(e)}'})
    return render(request, 'face_verify.html')

@login_required
@csrf_exempt
def face_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image', '')
            if not image_data:
                return JsonResponse({'success': False, 'message': 'Изображение не получено.'})
            print(f"Received image_data length: {len(image_data)}")

            # Декодируем base64 изображение
            try:
                image_data = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(image_data)
                print(f"Decoded image bytes length: {len(image_bytes)}")
                # Проверяем первые байты для определения формата
                if len(image_bytes) > 2:
                    print(f"First 2 bytes (hex): {image_bytes[:2].hex()}")
                    if image_bytes[:2] == b'\xff\xd8':
                        print("Detected JPEG format")
                    elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                        print("Detected PNG format")
                    else:
                        print("Unknown image format")
            except base64.binascii.Error as e:
                print(f"Base64 decode error: {str(e)}, image_data: {image_data[:50]}...")
                return JsonResponse({'success': False, 'message': f'Ошибка декодирования base64: {str(e)}'})

            # Сохраняем сырые байты для отладки
            raw_image_path = os.path.join('media', 'debug', f'face_login_raw_bytes_{request.user.username}.jpg')
            os.makedirs(os.path.dirname(raw_image_path), exist_ok=True)
            with open(raw_image_path, 'wb') as f:
                f.write(image_bytes)
            print(f"Raw bytes saved at: {raw_image_path}")

            # Открываем изображение с использованием потока
            try:
                image_stream = io.BytesIO(image_bytes)
                image = Image.open(image_stream)
                image.verify()  # Проверяем валидность
                image_stream.seek(0)  # Возвращаем указатель в начало
                image = Image.open(image_stream)  # Повторно открываем
                image_original = image.convert('RGB')  # Конвертируем в RGB
                image_np = np.array(image_original)  # Уберём нормализацию
                print(f"Image shape: {image_np.shape}, min: {image_np.min()}, max: {image_np.max()}")
            except Exception as e:
                print(f"Image validation error: {str(e)}, image_bytes length: {len(image_bytes)}")
                return JsonResponse({'success': False, 'message': f'Невалидное изображение: {str(e)}'})

            # Сохраняем оригинальное и необработанное изображение для отладки
            temp_image_original_path = os.path.join('media', 'debug', f'face_login_original_{request.user.username}.jpg')
            temp_image_raw_path = os.path.join('media', 'debug', f'face_login_raw_{request.user.username}.jpg')
            os.makedirs(os.path.dirname(temp_image_original_path), exist_ok=True)
            image_original.save(temp_image_original_path)
            Image.fromarray(image_np).save(temp_image_raw_path)
            print(f"Original image saved at: {temp_image_original_path}")
            print(f"Raw image saved at: {temp_image_raw_path}")

            # Извлекаем вектор лица
            try:
                captured_embedding = DeepFace.represent(
                    img_path=image_np,
                    model_name='Facenet',
                    enforce_detection=False,
                    detector_backend='dlib'
                )
                if not captured_embedding or not captured_embedding[0].get('embedding'):
                    print("DeepFace: No embedding found")
                    return JsonResponse({'success': False, 'message': 'Лицо не обнаружено. Убедитесь в хорошем освещении и правильном положении лица.'})
                captured_embedding = np.array(captured_embedding[0]['embedding'])
                print(f"Captured embedding shape: {captured_embedding.shape}, first 5 values: {captured_embedding[:5]}")
            except Exception as e:
                print(f"DeepFace error: {str(e)}")
                return JsonResponse({'success': False, 'message': f'Ошибка DeepFace: {str(e)}'})

            # Получаем сохранённый эмбеддинг пользователя
            try:
                face_encoding = FaceEncoding.objects.get(user=request.user)
                saved_embedding = face_encoding.get_encoding()
                if saved_embedding is None or len(saved_embedding) != 128:
                    print(f"Saved embedding invalid: length={len(saved_embedding) if saved_embedding is not None else 'None'}")
                    return JsonResponse({'success': False, 'message': 'Сохранённый Face ID повреждён.'})
                print(f"Saved embedding shape: {saved_embedding.shape}, first 5 values: {saved_embedding[:5]}")
            except FaceEncoding.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Face ID не зарегистрирован. Пожалуйста, зарегистрируйте Face ID через /face_verify/.'})

            # Сравниваем эмбеддинги с использованием евклидова расстояния
            if len(captured_embedding) != len(saved_embedding):
                print(f"Embedding size mismatch: captured={len(captured_embedding)}, saved={len(saved_embedding)}")
                return JsonResponse({'success': False, 'message': 'Ошибка: несоответствие размеров эмбеддингов.'})
            
            distance = np.sqrt(np.sum((captured_embedding - saved_embedding) ** 2))
            THRESHOLD = 5.0  # если что можно изменить этот порог между 4.0 и 6.0
            print(f"Verify result: distance={distance}, threshold={THRESHOLD}")

            if distance < THRESHOLD:
                request.session['face_verified'] = True
                messages.success(request, 'Face ID подтверждён!')
                os.remove(temp_image_original_path)
                os.remove(temp_image_raw_path)
                os.remove(raw_image_path)
                return JsonResponse({'success': True, 'message': 'Face ID подтверждён!', 'redirect': '/home/'})
            else:
                os.remove(temp_image_original_path)
                os.remove(temp_image_raw_path)
                os.remove(raw_image_path)
                return JsonResponse({'success': False, 'message': f'Лицо не распознано. Расстояние: {distance}. Попробуйте снова.'})

        except Exception as e:
            print(f"General error: {str(e)}")
            if os.path.exists(temp_image_original_path):
                os.remove(temp_image_original_path)
            if os.path.exists(temp_image_raw_path):
                os.remove(temp_image_raw_path)
            if os.path.exists(raw_image_path):
                os.remove(raw_image_path)
            return JsonResponse({'success': False, 'message': f'Ошибка обработки: {str(e)}'})
    return render(request, 'face_login.html')

@login_required
def diary_list(request):
    if not request.session.get('face_verified', False):
        return redirect('login')
    entries = DiaryEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'diary_list.html', {'entries': entries})

@login_required
def diary_create(request):
    if not request.session.get('face_verified', False):
        return redirect('login')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        photo = request.FILES.get('photo')
        if title and content:
            entry = DiaryEntry.objects.create(
                user=request.user,
                title=title,
                content=content,
                photo=photo
            )
            messages.success(request, 'Запись успешно создана!')
            return redirect('diary_list')
        else:
            messages.error(request, 'Заголовок и текст обязательны.')
    return render(request, 'diary_form.html')

@login_required
def diary_edit(request, pk):
    if not request.session.get('face_verified', False):
        return redirect('login')
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        photo = request.FILES.get('photo')
        if title and content:
            entry.title = title
            entry.content = content
            if photo:
                if entry.photo:
                    os.remove(entry.photo.path)
                entry.photo = photo
            entry.save()
            messages.success(request, 'Запись успешно обновлена!')
            return redirect('diary_list')
        else:
            messages.error(request, 'Заголовок и текст обязательны.')
    return render(request, 'diary_form.html', {'entry': entry})

@login_required
def diary_delete(request, pk):
    if not request.session.get('face_verified', False):
        return redirect('login')
    entry = get_object_or_404(DiaryEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        if entry.photo:
            os.remove(entry.photo.path)
        entry.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('diary_list')
    return render(request, 'diary_confirm_delete.html', {'entry': entry})