from pathlib import Path

def func1():
    my_string = "Mentoring, Metadata, Prototyping, Environment Art, Developing, Feedback, Unity, Oop, Postgresql, Spark, Unreal, Perforce, Substance Designer, Modo, 3ds Max, Validation Tools, Python, Xbox 360, Source Control, Rendering, Maya, Animation, AR, Front-end, Wordpress.com, CAD, Virtual Reality, Music Production, Augmented Reality, Computer Graphics, Software Engineer, Music Technology, Medical Simulation, Unreal Engine, Substance Painter, Substance Designer"
    array = my_string.split(", ")
    array.sort()
    print("\n".join(array))

def func2():
    my_path = Path(__file__).parent / "skills.txt"
    with my_path.open("r") as f:
        data = f.read()
    skills = data.split("\n")
    print(", ".join(skills))

func2()