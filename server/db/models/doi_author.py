from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional, Any, Union


from ..database import Base
from server.utils.function import isInt


class DOIAuthorGroup(Base):
    """
    DOI Author Group model.
    Represents a group of authors for DOI creation.
    """

    __tablename__ = "doi_author_group"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    userid = Column(Integer)
    name = Column(String)


class DOIAuthor(Base):
    """
    DOI Author model.
    Represents an author associated with a DOI.
    """

    __tablename__ = "doi_author"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    affiliation = Column(String)
    orcid = Column(String)
    gnd = Column(String)
    pos_order = Column(Integer)
    author_groupid = Column(Integer)

    @staticmethod
    def construct_creators(
        doi_group_id: Union[int, str], userid: int, db: Session
    ) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Construct a list of creators from a DOI author group.

        Args:
            doi_group_id: ID or name of the DOI author group
            userid: User ID of the requesting user
            db: Database session

        Returns:
            Tuple of (success, creators_list)
        """
        from sqlalchemy import and_

        if isInt(doi_group_id):
            # Filter by group ID
            authors = (
                db.query(DOIAuthor)
                .filter(
                    and_(
                        DOIAuthor.author_groupid == int(doi_group_id),
                        DOIAuthor.author_groupid == DOIAuthorGroup.id,
                        DOIAuthorGroup.userid == userid,
                    )
                )
                .order_by(DOIAuthor.id)
                .all()
            )
        else:
            # Filter by group name
            authors = (
                db.query(DOIAuthor)
                .filter(
                    and_(
                        DOIAuthor.author_groupid == DOIAuthorGroup.id,
                        DOIAuthorGroup.name == doi_group_id,
                        DOIAuthorGroup.userid == userid,
                    )
                )
                .order_by(DOIAuthor.id)
                .all()
            )

        if len(authors) == 0:
            return False, []

        creators = []
        for a in authors:
            a_dict = {"name": a.name, "affiliation": a.affiliation}
            if a.orcid:
                a_dict["orcid"] = a.orcid
            if a.gnd:
                a_dict["gnd"] = a.gnd
            creators.append(a_dict)

        return True, creators

    @staticmethod
    def authors_from_page(form_data):
        """
        Create author objects from form data.

        Args:
            form_data: Dictionary of form fields

        Returns:
            List of DOIAuthor objects
        """
        authors = []

        # Extract authors data from form
        author_ids = form_data.getlist("author_id")
        author_names = form_data.getlist("author_name")
        affiliations = form_data.getlist("affiliation")
        orcids = form_data.getlist("orcid")
        gnds = form_data.getlist("gnd")

        # Create authors
        for aid, an, aff, orc, gnd in zip(
            author_ids, author_names, affiliations, orcids, gnds
        ):
            if str(aid) == "" or str(aid) == "None":
                # New author
                authors.append(DOIAuthor(name=an, affiliation=aff, orcid=orc, gnd=gnd))
            else:
                # Existing author
                authors.append(
                    DOIAuthor(id=int(aid), name=an, affiliation=aff, orcid=orc, gnd=gnd)
                )

        return authors
