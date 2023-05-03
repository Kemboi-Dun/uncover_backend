from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Post, Upvote, Comment
from .serializers import PostSerializer, UpvoteSerializer, CommentSerializer
from django.contrib.auth.models import User


# Create your views here.
# functionalities present in this file include:

# Seeing all the blog posts
# Creating a new blog post
# Editing a blog post written by a particular user
# Deleting a blog post written by a particular user
# Seeing the blog posts written by a specific user
# Upvoting the post
# Adding a comment on the post


# Seeing all the blog posts
class PostListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status= status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = {
            "user": request.user.id,
            "title": request.data.get("title"),
            "body": request.data.get("body")
        }
        serializer = PostSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Creating a new blog post
class PostDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Post.objects.get(pk = pk)
        except Post.DoesNotExist:
            return None

    # Seeing the blog posts written by a specific user
    def get(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found!"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Editing a blog post written by a particular user
    def put(self, request, pk, *args, **kwargs):
        post=self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found!"}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "user": request.user.id,
            "title": request.data.get("title"),
            "body": request.data.get("body"),
            "upvote_count": post.upvote_count
        }
        serializer = PostSerializer(post, data=data, partial=True)
        if serializer.is_valid():
            if post.user.id == request.user.id:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"Error": "You are not authorized to edit this post"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Deleting a blog post written by a particular user
    def delete(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found!"}, status=status.HTTP_404_NOT_FOUND)
        if post.user.id == request.user.id:
            post.delete()
            return Response({"Res": "Object deleted!"},status=status.HTTP_200_OK)
        return Response({"Error": "You are not authorized to delete this post"},status=status.HTTP_401_UNAUTHORIZED)


class UserPostAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username, *args, **kwargs):
        user = User.objects.filter(username=username).first()
        if user is None:
            return  Response({"Error": "User not found!"}, status=status.HTTP_404_NOT_FOUND)
        posts = Post.objects.filter(user = user)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class UpvoteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self,pk):
        try:
            return Post.objects.get(pk = pk)
        except Post.DoesNotExist:
            return None

    # Upvoting the post
    def post(self, request, pk, *args, **kwargs):
        post=self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        upvoters=post.upvotes.all().values_list('user', flat=True)
        if request.user.id in upvoters:
            post.upvote_count -= 1
            post.upvotes.filter(user = request.user).delete()
        else:
            post.upvote_count += 1
            upvote = Upvote(user=request.user, post=post)
            upvote.save()
        post.save()
        serializer=PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return None

    def get(self,pk,request, *args, **kwargs):
        post=self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found!"}, status=status.HTTP_404_NOT_FOUND)
        comments=Comment.objects.filter(post=post)
        serializer=CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    # Adding a comment on the post
    def post(self,request,pk,*args,**kwargs):
        post=self.get_object(pk)
        if post is None:
            return Response({"Error": "Post not found!"}, status=status.HTTP_404_NOT_FOUND)
        data={
            "user":request.user.id,
            "post":post.id,
            "body": request.data.get("body")
        }
        serializer=CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
