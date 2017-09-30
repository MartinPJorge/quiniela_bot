from bs4 import BeautifulSoup
import requests
import re

class QuinielaScrapper:
    """Web scrapper to get 4chan thread messages"""

    # https://resultados.as.com/quiniela/2017_2018/jornada_10/

    def __init__(self):
        """Creates the scraper
        """
        self.url = 'http://4chan.org/'
        self.boardsURL = 'http://boards.4chan.org/'
        self.latestThread = None
        self.scraper = None

    def getFirstAtBoard(self, board):
        """Gets OP's message of first thread in the board

        :board: board where we'll get the thread

        :return: {'img': opPostImg,
               'title': opPostTitle, 
               'msg': opPostMsg,
               'no': opPostNo,
               'noLink': opPostNoLink}
        """
        print 'Getting in the scraper'
        fourChanBoard = requests.get(self.url + board)
        print 'Im done with request'
        fourChanBoard = fourChanBoard.text
        self.scraper = BeautifulSoup(fourChanBoard, "lxml") 
        print 'Scrapper retrieved!'

        board_ = self.scraper.select('div.board')[0]
        opPost = board_.select('div.opContainer')[2].select('div.op')[0]
        opPostMsg = str(opPost.select('blockquote.postMessage')[0])
        opPostImg = opPost.select('img')[0]['src'][2:]

        # Remove HTML tags
        lineBreaker = re.compile(r'<br/>')
        opPostMsg = lineBreaker.sub('\n', opPostMsg)
        tagBreaker = re.compile(r'<.*?>')
        opPostMsg = tagBreaker.sub('', opPostMsg)

        opPostInfo = opPost.select('div.postInfo')[0]
        opPostTitle = opPostInfo.select('span.subject')[0].text
        opPostNo = opPostInfo.select('span.postNum')[0].select('a')[0]['href']
        print opPostNo
        opPostNoLink = self.boardsURL + board + '/' + opPostNo
        opPostNo = opPostNo.split('#')[1]

        return {'img': opPostImg,
               'title': opPostTitle, 
               'msg': opPostMsg,
               'no': opPostNo,
               'noLink': opPostNoLink}
            

if __name__ == '__main__':
    scrap = FourChanScrapper()
    reto = scrap.getFirstAtBoard('pol')
    print(reto)

