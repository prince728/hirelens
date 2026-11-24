from pydantic import BaseModel,Field


class Contact(BaseModel):
    name:       str | None = None
    email:      str | None = None
    phone:      str | None = None
    location:   str | None = None
    links:      list[str] = Field(default_factory=list, description="GitHub, LinkedIn, portfolio URLs")

class Experience(BaseModel):
    company:str|None=None
    title:str|None=None
    start_date: str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date: str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")
    bullet_points: list[str]=Field(default_factory=list)

class Project(BaseModel): 
    name:str |None =None 
    technologies: list[str] = Feild(default_factory=list)
    start_date: str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date: str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")
    bullet_points: list[str]=Field(default_factory=list)


class Education(BaseModel): 
    institution: str | None=None
    degree:str | None=None
    field_of_study:str | None=None
    start_date: str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date: str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")



class Resume(BaseModel): 
    #the top-level piece that holds contact, summary, a list of skills, and lists of experience, projects, and education.
    contact:Contact = Field(default_factory=Contact)
    skills: list[str] = Field(default_factory=list, description="Individual skills, one per item")
    summary: str | None = None
    experience: list[Experience] = Field(default_factory= list,description="Paid jobs and internships only")
    projects:list[Project] = Field(default_factory= list)
    education: list[Education] = Field(default_factory= list)