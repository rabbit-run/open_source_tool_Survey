function validateSurveyForm()
{
var x=document.forms["survey_form"]["title"].value;
var y=document.forms["survey_form"]["question"].value;
var z=document.forms["survey_form"]["choices"].value;
if ((x==null || x=="")
  {
  alert("title must be filled out");
  return false;
  }
if (y==null || y=="")
{
    alert("question must be filled out");
    return false;
}
if (z==null || z==""))
{
    alert("choices must be filled out");
    return false;
} 
}

function validateManageForm()
{
    var x = document.forms["manage_form"]["key"].value;
    if (x ==null || x == "") {
        alert("must specify a survey");
        return false;
    }
}

