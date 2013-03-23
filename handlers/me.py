# encoding=utf-8

from storm.expr import (Desc, Asc, Select, Not)
import tornado.web
from base import BaseHandler

from models.database import User, LinkGroup, Link, FollowingUser, FollowingGroup, Comment
from settings import NUM_FEED
from tornado.escape import url_escape


class FeedHandler(BaseHandler):
    def get(self):
        follower_id = Select(FollowingUser.follower_id, (
            FollowingUser.user_id == self.current_user.id))
        group_id = Select(LinkGroup.id, (LinkGroup.user_id.is_in(follower_id)))
        links = self.db.find(Link, Link.group_id.is_in(
            group_id)).order_by(Desc(Link.updated))
        self.render("feed.html", links=links[:10], user=self.current_user)


class MyLinksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        sub = Select(LinkGroup.id, (LinkGroup.user_id == self.current_user.id))
        links = self.db.find(Link, Link.group_id.is_in(
            sub)).order_by(Desc(Link.updated))

        self.render("mylinks.html", links=links[:10], user=self.current_user)


class MeGroupHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, groupid):
        group = self.db.get(LinkGroup, int(groupid))
        link_id = Select(Link.id, (Link.group_id == int(group.id)))
        links = self.db.find(Link, Link.id.is_in(
            link_id)).order_by(Desc(Link.updated))
        self.render("megroup.html", group=group,
                    user=self.current_user, links=links)


class StaffPicksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        follower_id = Select(
            FollowingUser.follower_id, FollowingUser.user_id == self.current_user.id)
        staffs = self.db.find(User, Not(User.id.is_in(
            follower_id)), User.id != self.current_user.id).order_by(Desc(User.follower_count))
        self.render("staff_picks.html", staffs=staffs, user=self.current_user)


class PopularGroupsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        group_id = Select(
            FollowingGroup.group_id, FollowingGroup.user_id == self.current_user.id)
        group_id2 = Select(
            LinkGroup.id, LinkGroup.user_id == self.current_user.id)
        groups = self.db.find(LinkGroup, Not(LinkGroup.id.is_in(group_id)), Not(LinkGroup.id.is_in(
            group_id2)), LinkGroup.private == 0).order_by(Desc(LinkGroup.follower_count))
        self.render("popular_groups.html",
                    groups=groups, user=self.current_user)


class RecentLinksHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        group_id = Select(LinkGroup.id, (
            LinkGroup.user_id == self.current_user.id))
        links = self.db.find(Link, Not(Link.group_id.is_in(
            group_id))).order_by(Desc(Link.updated))
        print links.count()
        self.render("recent_links.html", links=links, user=self.current_user)


class AddGroupHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        self.render("addgroup.html", user=self.current_user, newgroup_msg="")

    @tornado.web.authenticated
    def post(self):
        group_name = self.get_argument('groupname')
        group_description = self.get_argument('group_description')
        group = self.db.find(
            LinkGroup,LinkGroup.user_id==self.current_user.id,LinkGroup.group_name==group_name).one()
        if not group:
            newgroup=LinkGroup()
            newgroup.user_id=self.current_user.id
            newgroup.group_name=group_name
            newgroup.description=group_description
            radio_value = self.get_argument('list-sharing')
            if radio_value == "private":
                newgroup.private = 1
            self.db.add(newgroup)
            self.db.commit()
            self.render("me.html", user=self.current_user)
        else:
            self.render("addgroup.html", user=self.current_user,
                        newgroup_msg="your group_name has existed,please try again")


class DeleteGroupHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self, group_id):
        link_id = Select(Link.id, (Link.group_id == int(group_id)))
        links = self.db.find(Link, Link.id.is_in(link_id))
        for link in links:
            self.db.remove(link)
        group = self.db.find(LinkGroup, LinkGroup.id == int(group_id)).one()
        self.db.remove(group)
        self.db.commit()
        self.render("me.html", user=self.current_user)


class EditGroupHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, group_id, previous_page):
        self.set_secure_cookie("previous", url_escape(previous_page))
        group = self.db.find(LinkGroup, LinkGroup.id == int(group_id)).one()
        self.render("editgroup.html", user=self.current_user,
                    group_name=group.group_name, group=group)

    @tornado.web.authenticated
    def post(self, group_id, previous_page):
        group_name = self.get_argument('groupname')
        group_description = self.get_argument('group_description')
        group = self.db.find(LinkGroup,LinkGroup.id==int(group_id)).one()
        group.group_name = group_name
        group.description=group_description
        radio_value = self.get_argument('list-sharing')
        if radio_value == "private":
            group.private = 1
        else:
            group.private = 0
        self.db.commit()
        self.redirect(previous_page)


class FollowingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        follower_id = Select(FollowingUser.follower_id, (
            FollowingUser.user_id == self.current_user.id))
        users = self.db.find(User, User.id.is_in(follower_id))
        group_id = Select(FollowingGroup.group_id, (
            FollowingGroup.user_id == self.current_user.id))
        groups = self.db.find(LinkGroup, LinkGroup.id.is_in(group_id))
        self.render("following.html", groups=groups,
                    users=users, user=self.current_user)


class FollowerHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = Select(FollowingUser.user_id, (
            FollowingUser.follower_id == self.current_user.id))
        users = self.db.find(User, User.id.is_in(user_id))
        self.render("follower.html", users=users, user=self.current_user)


class MeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("me.html", user=self.current_user)
