from myevents._job_event import JobEvent, Robot, Release, Job, StartInfo, Jobs
import json
import attr

# Note: both job.created.json and job.started.json are JSON files used to generate the schema for JobEvent
# This file illustrates how seemlessly they're imported and used as objects

with open('job.created.json') as f:
    j = json.load(f)
    jobCreated = JobEvent(**j)
# print(jobCreated)

# print the object as json
print(json.dumps(j, indent=4))
print(json.dumps(attr.asdict(jobCreated), indent=4))


with open('job.started.json') as f:
    j = json.load(f)
    jobStarted = Jobs(**j)
# print(jobStarted)

# print the object as json
print(json.dumps(j, indent=4))
print(json.dumps(attr.asdict(jobStarted), indent=4))