from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Bid, Comment


def index(request):
    activeListing = Listing.objects.filter(isActive=True)
    categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings" : activeListing,
        "categories" : categories
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def createListing(request):
    if request.method == "GET":
        categories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories" : categories
        })
    
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]

        currentUser = request.user

        categoryData = Category.objects.get(categoryName=category)

        newListing = Listing(
            title=title,
            description=description,
            imageUrl=imageurl,
            price=price,
            category=categoryData,
            owner=currentUser
        )
        newListing.save()

        return HttpResponseRedirect(reverse(index))
    
def displayCategory(request):
    if request.method == "POST":
        categoryForm = request.POST['category']
        category = Category.objects.get(categoryName=categoryForm)
        activeListings = Listing.objects.filter(isActive=True, category=category)
        categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings" : activeListings,
            "categories" : categories
        })
    
def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    if request.user.is_authenticated:
        userBid = Bid.objects.filter(user=request.user, listing=listingData).last()
    else:
        userBid=None
    return render(request, "auctions/listing.html", {
        "listing" : listingData,
        "isListingInWatchlist" : isListingInWatchlist,
        "allComments" : allComments,
        "isOwner" : isOwner,
        "userBid" : userBid
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isOwner = request.user.username == listingData.owner.username
    isListingInWatchlist = request.user in listingData.watchlist.all()
    userBid = Bid.objects.filter(user=request.user, listing=listingData).last()
    allComments = Comment.objects.filter(listing=listingData)
    return render(request, "auctions/listing.html", {
        "listing" : listingData,
        "isListingInWatchlist" : isListingInWatchlist,
        "allComments" : allComments,
        "isOwner" : isOwner,
        "update" : True,
        "message" : "Congratulations! Your auction is closed.",
        "userBid" : userBid
    })

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addBid(request, id):
    newBid = request.POST['newBid']
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    userBid = Bid.objects.filter(user=request.user, listing=listingData).last()
    if int(newBid) > listingData.price and listingData.isActive:
        updateBid = Bid(user=request.user, bid=int(newBid), listing=listingData)
        updateBid.save()
        userBid = Bid.objects.filter(user=request.user, listing=listingData).last()
        listingData.price = int(newBid)
        listingData.save()
        addWatchlist(request, id)
        return render(request, "auctions/listing.html", {
            "listing" : listingData,
            "message" : "Bid updated successfully",
            "update" : True,
            "isListingInWatchlist" : isListingInWatchlist,
            "allComments" : allComments,
            "isOwner" : isOwner,
            "userBid" : userBid
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing" : listingData,
            "message" : "Bid update failed",
            "update" : False,
            "isListingInWatchlist" : isListingInWatchlist,
            "allComments" : allComments,
            "isOwner" : isOwner,
            "userBid" : userBid
        })
    
def addComment(request, id):
    currentUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST['comment']

    newComment = Comment(
        author = currentUser,
        listing = listingData,
        message = message
    )

    newComment.save()

    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings" : listings
    })