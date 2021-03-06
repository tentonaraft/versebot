"""
#---------------------#
| VerseBot for reddit |
| By Matthieu Grieger |
#---------------------#
"""

from re import findall, search
from config import get_bot_username
import data
import helpers


class Verse:
	""" Class that holds the properties of a Bible verse, and various
	operations that go along with them. """
	
	_verse_data = list()
	_invalid_comment = False


	def __init__(self, verse_list, comment, permalink = False, subreddit = False):
		""" Initializes Verse object with data from the command(s).
		NOTE: permalink and subreddit are only used when dealing with
		a comment edit request. """
	
		for verse in verse_list:
			verse_book_num = data.get_book_number(verse.lower())
			if verse_book_num != False:
				try:
					verse_subreddit = comment.permalink[24:comment.permalink.find('/', 24)]
				except AttributeError:
					# This means we are dealing with a message, not a comment.
					verse_subreddit = subreddit
				verse_book_name = data.get_book_title(verse_book_num)
				verse_chapter = self._get_chapter_and_verse(verse.lower())[0]
				verse_selection = self._get_chapter_and_verse(verse.lower())[1]
				verse_translation = self._get_bible_translation(verse.upper(), verse_subreddit, verse_book_num)
				verse_content = helpers.get_verse_contents(verse_book_name, verse_book_num, verse_chapter, verse_selection, verse_translation)
				verse_title = helpers.get_verse_title()
				trans_title = helpers.get_translation_title()
				comment_author = str(comment.author)
				if permalink:
					comment_permalink = permalink
				else:
					comment_permalink = comment.permalink

				if verse_content != False:
					self._verse_data.append((verse_book_name, verse_chapter, verse_selection, verse_translation, verse_content, verse_subreddit, verse_title, trans_title, comment_author, comment_permalink))

		if len(self._verse_data) == 0:
			self._invalid_comment = True

		return


	def get_comment(self):
		""" Constructs a reddit comment. """
		
		if not self._invalid_comment:
			comment = ''
			for cur_ver_data in self._verse_data:
				book = cur_ver_data[0]
				chap = cur_ver_data[1]
				ver = cur_ver_data[2]
				translation = cur_ver_data[3]
				content = cur_ver_data[4]
				subreddit = cur_ver_data[5]
				context_link = self._get_context_link(book, chap, translation)
				verse_title = cur_ver_data[6]
				trans_title = cur_ver_data[7]
				comment_author = cur_ver_data[8]
				comment_permalink = cur_ver_data[9]

				comment += ('[**' + verse_title.lstrip() + ' | ' + trans_title.lstrip() + '**](' + context_link + ')\n>' + content) + '\n\n'

			if len(comment) > self._get_char_limit():
				comment = self._get_overflow_comment()
			comment += self._get_comment_footer(comment_author, comment_permalink)
			return comment
		else:
			return False

	
	def clear_verses(self):
		""" Clears contents of _verseData. """
		
		self._verse_data[:] = []
		return

	def get_verse_data(self):
		""" Simply returns _verse_data. """
		
		return self._verse_data

	
	def _get_chapter_and_verse(self, verse):
		""" Finds chapter number and verse number within current verse request. """
		
		chap = '0'
		ver = '0'

		if ':' in verse:
			chapter_and_verse = str(findall(r'\d+:\d*(?:-\d+)?', verse))
			chap = (chapter_and_verse.partition(':')[0])[2:]
			ver = (chapter_and_verse.partition(':')[2])[:-2]
		else:
			chap = str(findall(r'\s\d+', verse)).lstrip(' ')
			chap = chap[3:-2]

		return chap, ver

	
	def _get_bible_translation(self, comment_text, subreddit, book_num):
		""" Determines the correct Bible translation to use for the current verse.
		It first looks for a user-specified translation. If there is no
		translation specified, it will then use the default translation
		for the subreddit in which the comment was posted. """
	
		for translation in helpers.get_supported_translations():
			if search(r'\b' + translation + r'\b', comment_text):
				return translation
		return data.get_default_translation(subreddit, book_num)

	
	def _get_comment_footer(self, author, permalink):
		""" Simply returns the comment footer found at the bottom of every comment posted
		by the bot. """
	
		return ('\n***\n[^Source ^Code](https://github.com/matthieugrieger/versebot) ^|'
			   + ' [^/r/VerseBot](http://www.reddit.com/r/versebot) ^|'
			   + ' [^Contact ^Dev](http://www.reddit.com/message/compose/?to=mgrieger) ^|'
			   + ' [^FAQ](https://github.com/matthieugrieger/versebot/blob/master/docs/VerseBot%20Info.md#faq) ^|'
			   + ' [^Changelog](https://github.com/matthieugrieger/versebot/blob/master/docs/CHANGELOG.md) ^|'
			   + ' [^Statistics](http://matthieugrieger.com/versebot/) \n\n'
			   + ' ^All ^texts ^provided ^by [^BibleGateway](http://www.biblegateway.com) ^and [^TaggedTanakh](http://www.taggedtanakh.org) \n\n')
			   #+ ' ^**Mistake?** ^' + author + ' ^can [^edit](http://www.reddit.com/message/compose/?to=' + get_bot_username() +'&subject=edit&message={' + permalink + '} Please+enter+your+revised+verse+quotations+below+in+the+usual+bracketed+syntax.)' 
			   #+ ' ^or [^delete](http://www.reddit.com/message/compose/?to=' + get_bot_username() + '&subject=delete&message={' + permalink + '} This+action+cannot+be+reversed!) ^this ^comment.')


	def _get_context_link(self, book_name, chap, translation):
		""" Takes the verse's book name, chapter, and translation as parameters. The function
		then constructs a context link for the selected passage. This link appears on each
		verse title. """
	
		if translation == 'NJPS':
			return ('http://www.taggedtanakh.org/Chapter/Index/english-' + data.get_tanakh_name(book_name) + '-' + chap)
		else:
			return ('http://www.biblegateway.com/passage/?search=' + book_name + '%20' + chap
				+ '&version=' + translation).replace(' ', '%20')


	def _get_overflow_comment(self):
		""" Constructs and returns an overflow comment whenever the comment exceeds the character
		limit set by _get_char_limit(). Instead of posting the contents of the verse(s) in the comment,
		it links to webpages that contain the contents of the verse(s). """
		
		comment = 'The contents of the verse(s) you quoted exceed the character limit (' + str(self._get_char_limit()) + ' characters). Instead, here are links to the verse(s)!\n\n'
		for cur_ver_data in self._verse_data:
			book = cur_ver_data[0]
			chap = cur_ver_data[1]
			ver = cur_ver_data[2]
			translation = cur_ver_data[3]

			if translation == 'NJPS':
				overflow_link = ('http://www.taggedtanakh.org/Chapter/Index/english-' + data.get_tanakh_name(book) + '-' + chap)
			else:
				if ver != '0':
					overflow_link = ('http://www.biblegateway.com/passage/?search=' + book + '%20' + chap + ':' +
									ver + '&version=' + translation).replace(' ', '%20')
				else:
					overflow_link = ('http://www.biblegateway.com/passage/?search=' + book + '%20' + chap +
									 '&version=' + translation).replace(' ', '%20')

			if ver != '0':
				comment += ('- [' + book + ' ' + chap + ':' + ver + ' (' + translation + ')](' + overflow_link + ')\n')
			else:
				comment += ('- [' + book + ' ' + chap + ' (' + translation + ')](' + overflow_link + ')\n')

		return comment


	def _get_char_limit(self):
		""" Simply returns the current character limit for the reddit comment. Makes it easy to
		find/change in the future. NOTE: reddit's character limit is 10,000 characters by default. """
		
		return 6000
