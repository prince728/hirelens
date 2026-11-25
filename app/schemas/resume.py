from pydantic import BaseModel,Field


class Contact(BaseModel):
    name:               str | None = None
    email:              str | None = None
    phone:              str | None = None
    location:           str | None = None
    links:              list[str] = Field(default_factory=list, description="GitHub, LinkedIn, portfolio URLs")

class Skill(BaseModel):
    name:               str = Field(description="The skill exactly as written in the resume, for example React.js or PostgreSQL.")
    evidence:           str = Field(default="",description=(
                                    "One short line copied word for word from the resume that shows this skill. "
                                    "Never reword, shorten, or combine lines. "
                                    "Prefer a project or job bullet over the skills section. "
                                    "If no line mentions the skill, leave this empty."
                                    )
                                )

class Experience(BaseModel):
    company:            str|None=None
    title:              str|None=None
    start_date:         str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date:           str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")
    bullet_points:      list[str]=Field(default_factory=list)
    evidence:           str = Field(default="",description=(
                                    "The header line for this entry, copied word for word from the resume. "
                                    "Never reword. Leave empty if unsure."
                                    ),
                                )

class Project(BaseModel): 
    name:               str |None =None 
    technologies:       list[str] = Field(default_factory=list)
    start_date:         str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date:           str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")
    bullet_points:      list[str]=Field(default_factory=list)
    evidence:           str = Field(default="",description=(
                                    "The header line for this entry, copied word for word from the resume. "
                                    "Never reword. Leave empty if unsure."
                                    ),
                                )


class Education(BaseModel): 
    institution:        str | None=None
    degree:             str | None=None
    field_of_study:     str | None=None
    start_date:         str | None = Field(None, description="YYYY-MM, or YYYY if the month is not given")
    end_date:           str | None = Field(None, description="YYYY-MM, or 'Present' if ongoing")



class Resume(BaseModel): 
    contact:            Contact = Field(default_factory=Contact)
    skills:             list[Skill] = Field(default_factory=list, description="Individual skills, one per item")
    summary:            str | None = None
    experience:         list[Experience] = Field(default_factory= list,description="Paid jobs and internships only")
    projects:           list[Project] = Field(default_factory= list)
    education:          list[Education] = Field(default_factory= list)